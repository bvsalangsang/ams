from celery import shared_task
from django.core.cache import cache
from .models import PunchLog, EvaluatedPunchLog, SysPunchStatus, ManSchedule, CancelledSchedule
from django.db import connection
from collections import defaultdict
from datetime import datetime
import time

import requests
import json

@shared_task(bind=True)
def evaluate_punch_logs_task(self):
    task_id = self.request.id
    total_steps = 5 
    progress_key = f"eval_progress_{task_id}"
    logs = []
    percent = 0

    try:
        api_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
        response = requests.get(api_url)
        response.raise_for_status()
        users_raw = response.json().get("data", "[]")
        users = json.loads(users_raw)
        active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
        logs.append(f"✅ Fetched {len(active_users)} active users.")
    except Exception as e:
        logs.append(f"❌ API error: {str(e)}")
        cache.set(f"eval_progress_{self.request.id}", {"percent": 0, "logs": logs[-50:]}, timeout=3600)
        return {"status": "error", "logs": logs}

    if not active_users:
        logs.append("❌ No active users found.")
        cache.set(f"eval_progress_{self.request.id}", {"percent": 0, "logs": logs[-50:]}, timeout=3600)
        return {"status": "error", "logs": logs}

    punch_status, _ = SysPunchStatus.objects.get_or_create(
        punchName='punch_log_eval',
        defaults={'punchCount': '0', 'punchLastPkey': '', 'punchLastDate': None, 'isActive': 'Y'}
    )
    last_eval_date = punch_status.punchLastDate

    if last_eval_date:
        punchdates = PunchLog.objects.filter(
            punchdate__gt=last_eval_date
        ).values_list("punchdate", flat=True).distinct().order_by("punchdate")
    else:
        punchdates = PunchLog.objects.values_list("punchdate", flat=True).distinct().order_by("punchdate")

    # Collect all months/years needed for leave API calls
    months_years = set((d.month, d.year) for d in punchdates)
    all_leave_data = []
    for month, year in months_years:
        try:
            leave_response = requests.post(
                "https://hris.usep.edu.ph/api/dashboard/view-employee-leave?token=496871859d96697ba10536775445fd8f",
                data={"month": month, "year": year}
            )
            leave_response.raise_for_status()
            leave_data = leave_response.json().get("data", [])
            all_leave_data.extend(leave_data)
        except Exception:
            continue

    # Build leave map: {pds_users_id: {"FL": set(dates), "SL": set(dates), "VL": set(dates)}}
    leave_map = defaultdict(lambda: defaultdict(set))
    for entry in all_leave_data:
        uid = str(entry.get("pds_users_id"))
        for leave_type, field in [("FL", "force_leave_dates"), ("SL", "sick_leave_dates"), ("VL", "vacation_leave_dates")]:
            dates_str = entry.get(field, "")
            if dates_str:
                for d in dates_str.split(","):
                    try:
                        dt = datetime.strptime(d.strip(), "%b-%d-%Y").date()
                        leave_map[uid][leave_type].add(dt)
                    except Exception:
                        continue

    total_records = 0
    latest_processed_date = last_eval_date
    punchdate_count = len(punchdates)
    punchdate_idx = 0

    for punchdate in punchdates:
        punchdate_idx += 1
        logs.append(f"Processing {punchdate} ({punchdate_idx}/{punchdate_count})")
        percent = int((punchdate_idx / punchdate_count) * 100)
        # cache.set(f"eval_progress_{self.request.id}", {"percent": percent, "logs": logs[-50:]}, timeout=3600)
        cache.set(progress_key, {
            "percent": percent,
            "logs": logs[-5:],  # keep last 5 logs only
        }, timeout=3600) 

        event_nos = PunchLog.objects.filter(punchdate=punchdate).values_list("eventNo", flat=True).distinct()
        cancelled_events = set(
            ManSchedule.objects.filter(
                schedId__in=CancelledSchedule.objects.filter(cancelledDate=punchdate).values_list('schedId', flat=True)
            ).values_list('eventNo', flat=True)
        )
        schedule_map = {
            str(s.eventNo): s for s in ManSchedule.objects.filter(eventNo__in=event_nos)
        }

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT punchNo, empId, pdsId, employee, eventNo, punchdate,
                    punchTimeIn, punchTimeOut, latitude, longitude,
                    officeId, office, systemDateTime
                FROM punch_log
                WHERE punchdate = %s AND isActive = 'Y'
            """, [punchdate])
            punch_logs_raw = cursor.fetchall()

        log_map = {
            (str(row[2]), str(row[4])): row for row in punch_logs_raw
        }

        evaluated_records = []

        for  emp in active_users:
            emp_id = str(emp.get("id"))
            emp_name = emp.get("NAME")
            empStatus = emp.get("EMPLOYMENT_STATUS")
            empType = emp.get("EMPLOYMENT_TYPE")
            empRank = emp.get("EMPLOYMENT_RANK")
            office_id = str(emp.get("DEPARTMENT_ID"))
            office = emp.get("DEPARTMENT")
            campusId = emp.get("CAMPUS_ID")
            campus = emp.get("CAMPUS")

            for event_no in event_nos:
                key = (emp_id, str(event_no))
                is_cancelled = str(event_no) in cancelled_events
                sched = schedule_map.get(str(event_no))

                # --- LEAVE CHECK ---
                leave_type = None
                for lt in ("FL", "SL", "VL"):
                    if punchdate in leave_map.get(emp_id, {}).get(lt, set()):
                        leave_type = lt
                        break

                if leave_type:
                    msg = f"🟡 Leave ({leave_type}): {emp_name} [{event_no}]"
                    record = EvaluatedPunchLog(
                        punchNo='n/a',
                        empId=emp_id,
                        pdsId=emp_id,
                        employee=emp_name,
                        empStatus=empStatus,
                        empType=empType,
                        empRank=empRank,
                        eventNo=event_no,
                        punchdate=punchdate,
                        punchTimeIn=leave_type,
                        punchTimeOut=leave_type,
                        latitude="0.0",
                        longitude="0.0",
                        officeId=office_id,
                        office=office,
                        campusId=campusId,
                        campus=campus,
                        isActive='Y',
                        attStatusId="4",
                        remarks=leave_type,
                        systemDateTime=None
                    )
                elif key in log_map:
                    row = log_map[key]
                    msg = f"✅ Present: {emp_name} [{event_no}]"
                    record = EvaluatedPunchLog(
                        punchNo=row[0],
                        empId=emp_id,
                        pdsId=row[2],
                        employee=emp_name,
                        empStatus=empStatus,
                        empType=empType,
                        empRank=empRank,
                        eventNo=event_no,
                        punchdate=row[5],
                        punchTimeIn=row[6],
                        punchTimeOut=row[7],
                        latitude=row[8],
                        longitude=row[9],
                        officeId=office_id,
                        office=office,
                        campusId=campusId,
                        campus=campus,
                        isActive='Y',
                        attStatusId="1",
                        remarks="",
                        systemDateTime=row[12]
                    )
                else:
                    punch_in = "Absent"
                    punch_out = "Absent"
                    att_status = "2"
                    remarks = ""
                    if is_cancelled and sched:
                        if sched.startTime and sched.startTime != "00:00:00":
                            punch_in = "cancelled"
                        if sched.endTime and sched.endTime != "00:00:00":
                            punch_out = "cancelled"
                        att_status = "3"
                        remarks = "Schedule cancelled."
                    msg = f"❌ Absent: {emp_name} [{event_no}]" if not is_cancelled else f"🚫 Cancelled: {emp_name} [{event_no}]"
                    record = EvaluatedPunchLog(
                        punchNo='n/a',
                        empId=emp_id,
                        pdsId=emp_id,
                        employee=emp_name,
                        empStatus=empStatus,
                        empType=empType,
                        empRank=empRank,
                        eventNo=event_no,
                        punchdate=punchdate,
                        punchTimeIn=punch_in,
                        punchTimeOut=punch_out,
                        latitude="0.0",
                        longitude="0.0",
                        officeId=office_id,
                        office=office,
                        campusId=campusId,
                        campus=campus,
                        isActive='Y',
                        attStatusId=att_status,
                        remarks=remarks,
                        systemDateTime=None
                    )
                evaluated_records.append(record)
                logs.append(msg)
              
            

        EvaluatedPunchLog.objects.bulk_create(evaluated_records, batch_size=500)
        total_records += len(evaluated_records)
        latest_processed_date = punchdate
        logs.append(f"✅ Finished {punchdate} ({punchdate_idx}/{punchdate_count})")
        percent = int((punchdate_idx / punchdate_count) * 100)
        cache.set(f"eval_progress_{self.request.id}", {"percent": percent, "logs": logs[-50:]}, timeout=3600)

    # Update SysPunchStatus
    if latest_processed_date:
        punch_status.punchLastPkey = ""
        punch_status.punchLastDate = latest_processed_date
        punch_status.punchCount = str(EvaluatedPunchLog.objects.count())
        punch_status.save()

    logs.append(f"✅ Evaluation complete. {total_records} records evaluated.")
    # cache.set(f"eval_progress_{self.request.id}", {"percent": 100, "logs": logs[-50:]}, timeout=3600)
    cache.set(progress_key, {
        "percent": 100,
        "logs": logs[-5:]
    }, timeout=3600)
    return {"status": "done", "logs": logs}