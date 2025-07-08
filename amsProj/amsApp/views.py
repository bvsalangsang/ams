from django.utils import timezone
from django.db import connection
from django.http import JsonResponse,HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.apps import apps
from django.db.models import Max
import requests
import json
from datetime import datetime
from .sqlcommands import * 
from .sqlparams import *
from .forms import *    

def dashboard(request):
    return render(request, 'amsApp/dashboard.html')

def attendanceLogs(request):
    return render(request, 'amsApp/attendance-log.html')

def attJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fecthAttendanceLogs())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "punchNo":row[0],
            "eventName":row[1],
            "empId":row[2],
            "pdsId":row[3],
            "employee":row[4],
            "office":row[5],
            "punchdate":row[6],
            "punchTimeIn":row[7],
            "punchTimeOut":row[8],
            "latitude":row[9],
            "longitude":row[10],
            "systemDateTime":row[11]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

def attJsonListByOfficeRange(request):
    start_date = request.GET.get("start_date_office") or request.POST.get("start_date_office")
    end_date = request.GET.get("end_date_office") or request.POST.get("end_date_office")

    filterQuery = ""
    params = []

    # If no dates, fetch all logs
    if start_date and end_date:
        filterQuery += " AND pch.punchDate BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    
    with connection.cursor() as cursor:
        cursor.execute(fetchAttendanceLogsByDateRange(filterQuery), params)
        rows = cursor.fetchall()

    office_dict = defaultdict(lambda: defaultdict(list))
    for row in rows:
        office = row[5] or "Unknown"
        emp_id = str(row[2]).strip()
        employee = str(row[4]).strip()
        emp_key = f"{emp_id}|{employee}"
        log = {
            "punchdate": row[6],
            "punchTimeIn": row[7],
            "punchTimeOut": row[8],
            "latitude": row[9],
            "longitude": row[10],
            "punchNo": row[0],
            "eventName": row[1],
            "pdsId": row[3],
            "systemDateTime": row[12],
            "officeId": row[11],
            "isActive": row[13],
        }
        office_dict[office][emp_key].append(log)
    result = {office: dict(emp_logs) for office, emp_logs in office_dict.items()}
    return JsonResponse(result, safe=False)

def attendanceByOfficeView(request):
    return render(request, 'amsApp/attendance.html')

def attendanceView(request):
    events = ManEvent.objects.raw(fetchQueryEvent())
    return render(request, 'amsApp/attendance-view.html',{'events': events})

def attJsonListByEvent(request):
    eventNo = request.GET.get("eventNo")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    filterQuery = ""
    params = []

    if start_date and end_date and eventNo:
        filterQuery += " AND pch.punchDate BETWEEN %s AND %s AND pch.eventNo = %s"
        params.extend([start_date, end_date, eventNo])
    elif start_date and end_date:
        filterQuery += " AND pch.punchDate BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    elif eventNo:
        filterQuery += " AND pch.eventNo = %s"
        params.append(eventNo)

    with connection.cursor() as cursor:
        cursor.execute(fetchAttendaceByEvent(filterQuery), params)
        rows = cursor.fetchall()

    grouped = defaultdict(list)
    for row in rows:
        punchNo = row[0]
        eventName = row[1]
        empId = row[2]
        pdsId = row[3]
        employee = row[4]
        office = row[5]
        punchDate = row[6]
        punchTimeIn = row[7]
        punchTimeOut = row[8]
        latitude = row[9]
        longitude = row[10]
        systemDateTime = row[11]
        isActive = row[12]

        grouped[eventName].append({
            "punchNo": punchNo,
            "empId": empId,
            "pdsId": pdsId,
            "employee": employee,
            "office": office,
            "punchDate": str(punchDate),
            "punchTimeIn": punchTimeIn,
            "punchTimeOut": punchTimeOut,
            "latitude": latitude,
            "longitude": longitude,
            "systemDateTime": str(systemDateTime) if systemDateTime else None,
            "isActive": isActive,
        })

    result = []
    for event, punches in grouped.items():
        result.append({
            "eventName": event,
            "records": punches
        })

    return JsonResponse({"data": result}, safe=False)
# getting Pkeys
ALLOWED_MODELS = [
    'ManShift', 'ManShiftType', 'ManShiftBreak', 'PunchLog', 'sysInfo',
    'ManEvent', 'ManEventType', 'ManLocation', 'ManLocationDet', 'ManSchedule'
]

def getNextPkeyId(request):
    
    model_name = request.GET.get('model')
    if not model_name:
        return HttpResponseBadRequest("Missing 'model' parameter.")
    
    if model_name not in ALLOWED_MODELS:
        return HttpResponseBadRequest("Model access is not allowed.")

    try:
        model = apps.get_model('amsApp', model_name)
    except LookupError:
        return HttpResponseBadRequest(f"Model '{model_name}' not found.")

    pk_field = model._meta.pk.name
    pk_field_type = model._meta.get_field(pk_field).get_internal_type()

    # Only support integer-based primary keys for now
    if pk_field_type not in ['AutoField', 'BigAutoField', 'IntegerField']:
        return HttpResponseBadRequest(f"Unsupported primary key type: {pk_field_type}")

    try:
       latest = model.objects.aggregate(max_id=Max(pk_field))['max_id']
       next_id = (latest + 1) if latest else 1
    except Exception as e:
        return HttpResponseBadRequest("Failed to retrieve next primary key.")

    return JsonResponse({'next_id': next_id, 'pk_field': pk_field})

#shift 
@csrf_exempt
def shiftSaveUpdate(request):
    if request.method == "POST":
        try:
            shift = shiftParams()  

            
            shift["shiftNo"] = request.POST.get("shiftNo", "")
            shift["shiftName"] = request.POST.get("shiftName", "")
            shift["shiftTypeNo"] = request.POST.get("shiftTypeNo", "")
            shift["breakNo"] = request.POST.get("breakNo", "")
            shift["description"] = request.POST.get("description", "")
            shift["startTime"] = request.POST.get("startTime", "")
            shift["endTime"] = request.POST.get("endTime", "")
            shift["isActive"] = request.POST.get("isActive", "Y")  # Default to active

            sql_query = saveUpdateShift()
            params = (
                shift["shiftNo"], shift["shiftName"], shift["shiftTypeNo"],
                shift["breakNo"], shift["description"], shift["startTime"],
                shift["endTime"], shift["isActive"]
            )

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Saved"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})
    else:
       return JsonResponse({"Status": "Wrong Request"})
 
def deleteShiftView(request):
    if request.method == "POST":
        try:
            shiftNo = request.POST.get("shiftNo")
            if not shiftNo:
                return JsonResponse({"Status": "Error", "Message": "Missing shiftNo"})

            sql_query = deleteShift()
            params = (shiftNo,)

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Deleted"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})

def shiftJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchShift())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "shiftNo":row[0],
            "shiftName":row[1],
            "shiftTypeNo":row[2],
            "breakNo":row[3],
            "description":row[4],
            "startTime":row[5],
            "endTime":row[6]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

def shiftTypeView(request):
    return render(request, 'amsApp/event-type.html')

def shiftTypeJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchShiftType())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "shiftTypeNo":row[0],
            "shiftType":row[1]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

@csrf_exempt
def shiftTypeSaveUpdate(request):
    if request.method == "POST":
        try:
            shiftType = shiftTypeParams()  
            
            shiftType["shiftTypeNo"] = request.POST.get("shiftTypeNo", "")
            shiftType["shiftType"] = request.POST.get("shiftType", "")
            shiftType["isActive"] = request.POST.get("isActive", "Y")  # Default to active

            sql_query = saveUpdateShiftType()
            params = (
                shiftType["shiftTypeNo"], shiftType["shiftType"], shiftType["isActive"]
            )

            print(sql_query, params)
            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Saved"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})

@csrf_exempt
def deleteShiftType(request):
    if request.method == "POST":
        try:
            shiftTypeNo = request.POST.get("shiftTypeNo")
            if not shiftTypeNo:
                return JsonResponse({"Status": "Error", "Message": "Missing shiftNo"})

            sql_query = deleteSQueryShiftType()
            params = (shiftTypeNo,)
            print(sql_query, params)

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Deleted"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})

# event 
def eventView(request):
    eventform = EventForm()
    eventList = ManEventType.objects.raw(fetchQueryEventType())
    return render(request, 'amsApp/event.html', {'form':eventform, 'eventList':eventList})  

def eventJsonList(request): 
    with connection.cursor() as cursor:
        cursor.execute(fetchQueryEvent())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "eventNo":row[0],
            "eventName":row[1],
            "eventType":row[2],
            "description":row[3],
            "isActive":row[4]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

@csrf_exempt
def eventSaveUpdateParams(request):
   
    if request.method == "POST":
        try:
            event = eventParams()  

            event["eventNo"] = request.POST.get("eventNo", "")
            event["eventName"] = request.POST.get("eventName", "")
            event["eventTypeNo"] = request.POST.get("eventTypeNo", "")
            event["description"] = request.POST.get("description", "")
            event["isActive"] ="Y" # Default to active

            sql_query = saveUpdateQueryEvent()
            params = (
                event["eventNo"], 
                event["eventName"],
                event["eventTypeNo"], 
                event["description"],
                event["isActive"]
            )

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Saved"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})
    else:
        return JsonResponse({"Status": "Wrong Request"})
    
def deleteEvent(request):
    if request.method == "POST":
        try:
            eventNo = request.POST.get("eventNo")
            if not eventNo:
                return JsonResponse({"Status": "Error", "Message": "Missing eventNo"})

            sql_query = delQueryEvent()
            params = (eventNo,)
            print(sql_query, params)

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Deleted"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})

# Event Type
def eventTypeView(request):
    form = EventTypeForm()
    return render(request, 'amsApp/event-type.html', {'form':form})

def eventTypeJsonList(request): 
    with connection.cursor() as cursor:
        cursor.execute(fetchQueryEventType())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "eventTypeNo":row[0],
            "eventType":row[1],
            "isActive":row[2]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

@csrf_exempt
def eventTypeSaveUpdate(request):
    if request.method == "POST":
        try:
            eventType = eventTypeParams()  

            eventType["eventTypeNo"] = request.POST.get("eventTypeNo", "")
            eventType["eventType"] = request.POST.get("eventType", "")
            eventType["isActive"] = "Y" 

            sql_query = saveUpdateQueryEventType()
            params = (
                eventType["eventTypeNo"], 
                eventType["eventType"], 
                eventType["isActive"]
            )

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Saved"})
        except Exception as err:
            print("error:" + str(err))
            return JsonResponse({"Status": "Error", "Message": str(err)})
    else:
        return JsonResponse({"Status": "Wrong Request"})
@csrf_exempt
def deleteEventType(request):
    if request.method == "POST":
        try:
            eventTypeNo = request.POST.get("eventTypeNo")
            if not eventTypeNo:
                return JsonResponse({"Status": "Error", "Message": "Missing eventTypeNo"})

            sql_query = delQueryEventType()
            params = (eventTypeNo,)

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Deleted"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})
 
#schedule
def scheduleView(request):
    form = ScheduleForm()
    events = ManEvent.objects.raw(fetchQueryEvent())
    locations = ManLocation.objects.raw(fetchQueryLocationOnly())
    return render(request, 'amsApp/schedule.html', {'form':form, 'events':events, 'locations':locations})

def scheduleJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchQuerySchedule())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "schedId": row[0],
            "locName": row[1],
            "eventName": row[2],
            "startDate": row[3] if row[3] else "0000-00-00",
            "endDate": row[4] if row[4] else "0000-00-00",
            "startTime": row[5] if row[5] else "00:00",
            "startGrace": row[6] if row[5] else "00",
            "endTime": row[7] if row[7] else "00:00",
            "endGrace": row[8] if row[8] else "00",
            "recurrenceType": row[9],
            "recurrenceDays": row[10],
            "dateCreated": str(row[11]) if row[11] else None,
            "isRecurring": row[12],
            "isSet": row[13],
            "isActive": row[14],
       
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)

@csrf_exempt
def scheduleSaveUpdate(request):
    if request.method != "POST":
        return JsonResponse({"Status": "Wrong Request"})

    try:
        schedule = scheduleParams()

        # Helper to get POST with fallback
        def get_post(key, default=""):
           val = request.POST.get(key)
           return val.strip() if val and val.strip() else None

        # Assign fields with defaults
        schedule["schedId"] = get_post("schedId")
        schedule["locationId"] = get_post("locationId")
        schedule["eventNo"] = get_post("eventNo")
        schedule["startDate"] = get_post("startDate") 
        schedule["endDate"] = get_post("endDate") 
        schedule["startTime"] = get_post("startTime") or "00:00"
        schedule["startGrace"] = get_post("startGrace") or "00"
        schedule["endTime"] = get_post("endTime") or "00:00"
        schedule["endGrace"] = get_post("endGrace") or "00"
        schedule["recurrenceType"] = get_post("recurrenceType")
        schedule["recurrenceDays"] = ",".join(request.POST.getlist("recurrenceDays"))
        schedule["isRecurring"] = get_post("isRecurring", "N").upper()
        schedule["isSet"] = "N"
        schedule["isActive"] = "Y"

        # SQL query and params
        sql_query = saveUpdateQuerySchedule()
        params = (
            schedule["schedId"],
            schedule["locationId"],
            schedule["eventNo"],
            schedule["startDate"],
            schedule["endDate"],
            schedule["startTime"],
            schedule["startGrace"],
            schedule["endTime"],
            schedule["endGrace"],
            schedule["recurrenceType"],
            schedule["recurrenceDays"],
            schedule["isRecurring"],
            schedule["isSet"],
            schedule["isActive"],
        )

        with connection.cursor() as cursor:
            cursor.execute(sql_query, params)

        return JsonResponse({"Status": "Saved"})

    except Exception as err:
        return JsonResponse({"Status": "Error", "Message": str(err)})
    
#set schedule
def setScheduleView(request):
    return render(request, 'amsApp/set-schedule.html')

@csrf_exempt
def setSchedule(request):
    if request.method == "POST":
        try:
            schedId = request.POST.get("schedId")
            isSet = request.POST.get("isSet")  # <-- get isSet from POST
            if not schedId or isSet not in ("Y", "N"):
                return JsonResponse({"Status": "Error", "Message": "Missing or invalid schedId or isSet"})

            sql_query = setQuerySchedule()
            params = (isSet, schedId)  # <-- pass both isSet and schedId

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

            return JsonResponse({"Status": "Set Schedule"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})

    return JsonResponse({"Status": "Wrong Request"})

#location
def locationView(request):
    mapForm = LocationForm()
    return render(request, 'amsApp/location.html',{'mapForm':mapForm})

def locationJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchQueryLocation())
        rows = cursor.fetchall()

    locations = {}
    for row in rows:
        locationId, locName, address, isActive, longitude, latitude = row
        if locationId not in locations:
            locations[locationId] = {
                "locationId": locationId,
                "locName": locName,
                "address": address,
                "isActive": isActive,
                "coordinates": []
            }
        if longitude is not None and latitude is not None:
            locations[locationId]["coordinates"].append({
                "longitude": longitude,
                "latitude": latitude
            })

    # Convert the locations dict to a list for JSON response
    jsonResultData = list(locations.values())
    return JsonResponse({"data": jsonResultData}, safe=False)

@csrf_exempt
def saveLocation(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            locationId = data.get("locationId", "")
            locName = data.get("locName", "")
            address = data.get("address", "")
            isActive = data.get("isActive", "Y")
            coords = data.get("coords", [])
            saveType = request.GET.get("saveType")

            print("saveType:", saveType)

            # Save main location
            sql_query = saveUpdateQueryLocation()
            params = (locationId, locName, address, isActive)
            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)
            
            if saveType == "update":
                # Delete existing coordinates for this location
                del_sql = delQueryLocationDet()
                with connection.cursor() as cursor:
                    cursor.execute(del_sql, (locationId,))  

            # Save coordinates (polygon points) - ctrlNo is auto-increment
            sql_det = saveQueryLocationDet()
            with connection.cursor() as cursor:
                for coord in coords:
                    cursor.execute(sql_det, (locationId, coord['longitude'], coord['latitude'], 'Y'))
       
            return JsonResponse({"Status": "Saved"})
        except Exception as err:
            return JsonResponse({"Status": "Error", "Message": str(err)})
    else:
        return JsonResponse({"Status": "Wrong Request"})

# dashboard functions
def getDashTotalRecords(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 1. Total Registered Employee (all time, isActive='Y')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT empId)
            FROM punch_log
            WHERE isActive='Y'
        """)
        total_registered_employee = cursor.fetchone()[0] or 0

    # Prepare dynamic SQL and params for the rest
    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "AND punchDate BETWEEN %s AND %s"
        params = [start_date, end_date]

    # 2. Total Presents (unique empId, isActive='Y', optional date range)
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(DISTINCT empId)
            FROM punch_log
            WHERE isActive='Y' {date_filter}
        """, params)
        total_presents = cursor.fetchone()[0] or 0

    # 3. Total Offices (unique, non-null officeId, isActive='Y', optional date range)
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(DISTINCT officeId)
            FROM punch_log
            WHERE isActive='Y' AND officeId IS NOT NULL AND officeId != '' {date_filter}
        """, params)
        total_offices = cursor.fetchone()[0] or 0

    # 4. Total Events (unique eventNo, isActive='Y', optional date range)
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(DISTINCT eventNo)
            FROM punch_log
            WHERE isActive='Y' {date_filter}
        """, params)
        total_events = cursor.fetchone()[0] or 0

    data = {
        "total_registered_employee": total_registered_employee,
        "total_presents": total_presents,
        "total_offices": total_offices,
        "total_events": total_events,
    }
    return JsonResponse(data)

def getDashAttendance(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "AND punchDate BETWEEN %s AND %s"
        params = [start_date, end_date]

    # PunchTimeIn per week
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT YEAR(punchDate) AS year, WEEK(punchDate, 1) AS week, COUNT(*) AS count
            FROM punch_log
            WHERE isActive='Y' AND punchTimeIn IS NOT NULL AND punchTimeIn != '' {date_filter}
            GROUP BY year, week
            ORDER BY year, week
        """, params)
        punchin_rows = cursor.fetchall()

    # PunchTimeOut per week
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT YEAR(punchDate) AS year, WEEK(punchDate, 1) AS week, COUNT(*) AS count
            FROM punch_log
            WHERE isActive='Y' AND punchTimeOut IS NOT NULL AND punchTimeOut != '' {date_filter}
            GROUP BY year, week
            ORDER BY year, week
        """, params)
        punchout_rows = cursor.fetchall()

    # Format week as "YYYY-WW"
    punchin_data = [{"week": f"{row[0]}-W{row[1]:02d}", "count": row[2]} for row in punchin_rows]
    punchout_data = [{"week": f"{row[0]}-W{row[1]:02d}", "count": row[2]} for row in punchout_rows]

    return JsonResponse({
        "punchTimeIn": punchin_data,
        "punchTimeOut": punchout_data
    })

def getDashEventPart(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "AND p.eventNo IS NOT NULL AND p.punchDate BETWEEN %s AND %s"
        params = [start_date, end_date]
    else:
        date_filter = "AND p.eventNo IS NOT NULL"

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT p.eventNo, COALESCE(e.eventName, 'Unknown Event') AS eventName, COUNT(DISTINCT p.empId) AS participant_count
            FROM punch_log p
            LEFT JOIN man_event e ON p.eventNo = e.eventNo
            WHERE p.isActive='Y' {date_filter}
            GROUP BY p.eventNo, e.eventName
            ORDER BY participant_count DESC
        """, params)
        rows = cursor.fetchall()

    data = [
        {
            "eventNo": row[0],
            "eventName": row[1],
            "count": row[2]
        }
        for row in rows if row[0]
    ]

    return JsonResponse({"participation": data})

def getDashOffice(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "AND punchDate BETWEEN %s AND %s"
        params = [start_date, end_date]

    # Group by office (name), for all events, filtered by date if provided
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT office, COUNT(DISTINCT empId) AS punch_count
            FROM punch_log
            WHERE isActive='Y' {date_filter}
            GROUP BY office
            ORDER BY punch_count DESC
        """, params)
        rows = cursor.fetchall()

    data = [
        {
            "office": row[0] if row[0] else "Unknown",
            "count": row[1]
        }
        for row in rows
    ]

    return JsonResponse({"offices": data})

def getDashPunchesByWeekday(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "AND punchDate BETWEEN %s AND %s"
        params = [start_date, end_date]

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT 
                DAYNAME(punchDate) AS weekday,
                DAYOFWEEK(punchDate) AS weekday_num,
                COUNT(*) AS count
            FROM punch_log
            WHERE isActive='Y' {date_filter}
            GROUP BY weekday, weekday_num
            ORDER BY weekday_num
        """, params)
        rows = cursor.fetchall()

    data = [
        {"weekday": row[0], "count": row[2]}
        for row in rows
    ]
    return JsonResponse({"punches_by_weekday": data})

# API parsing 
def fetchAndParseUsers(request):
    api_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"

    try:
        response = requests.get(api_url)
        response.raise_for_status()  

        json_response = response.json()

        users_raw = json_response.get('data', '[]')
        users = json.loads(users_raw)  # Now it's a list of dicts
     
        names = [user.get("NAME", "") for user in users]

        # return JsonResponse({
        #     "status": "success",
        #     "count": len(users),
        #     "names": names,
        #     "pretty_users": users
        # }, json_dumps_params={'indent': 2})  # Pretty-printing in response

        return JsonResponse({
                    "status": "success",
                    "count": len(users),
                    "usep_users": users
                }, json_dumps_params={'indent': 2}) 
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def check_attendance(event_no=None, target_date=None):
    # Map eventNo to the field we want to check
    event_requirements = {
        "1": "punchTimeIn",   # Flag Ceremony
        "2": "punchTimeOut",  # Flag Retreat
    }

    required_field = event_requirements.get(str(event_no), "punchTimeIn")

    # 1st API: Employee master list
    hris_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
    hris_res = requests.get(hris_url).json()
    master_list = json.loads(hris_res.get("data", "[]"))

    # 2nd API: All punch logs
    punch_url = "http://127.0.0.1:8000/dashboard/api/get-data-punch"
    punch_res = requests.get(punch_url).json()
    punch_logs = punch_res if isinstance(punch_res, list) else [punch_res]

    # Filter logs by event and date if provided
    if event_no and target_date:
        filtered_logs = [
            log for log in punch_logs
            if str(log.get("eventNo")) == str(event_no) and log.get("punchdate") == target_date
        ]
    else:
        filtered_logs = punch_logs

    full_result = []

    for emp in master_list:
        emp_id = str(emp.get("id"))
        log = None  # Initialize log for safe fallback

        # Find logs for employee
        matching_logs = [
            l for l in filtered_logs if str(l.get("pdsId")) == emp_id
        ]

        if matching_logs:
            for log in matching_logs:
                is_present = log.get(required_field) != "00:00:00"
                log["status"] = "Present" if is_present else "Absent"
                full_result.append(log)
        else:
            full_result.append({
                "punchNo": None,
                "eventNo": event_no,
                "empId": None,
                "pdsId": emp_id,
                "employee": emp.get("NAME"),
                "punchdate": target_date or "Unknown",
                "punchTimeIn": "00:00:00",
                "punchTimeOut": "00:00:00",
                "latitude": None,
                "longitude": None,
                "officeId": None,
                "office": emp.get("DEPARTMENT"),
                "systemDateTime": datetime.now().isoformat(),  # fallback timestamp
                "isActive": "N",
                "status": "Absent"
            })
    return full_result

def api_attendance_json(request):
    event_no = request.GET.get("eventNo")     # optional
    target_date = request.GET.get("date")     # optional
    result = check_attendance(event_no, target_date)
    return JsonResponse(result, safe=False, json_dumps_params={'indent': 2})

#print 
def printView(request):
    return render(request, 'amsApp/print.html')

