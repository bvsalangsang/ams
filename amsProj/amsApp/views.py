from django.utils import timezone
from django.db import connection
from django.http import JsonResponse,HttpResponseBadRequest,HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.apps import apps
from django.db.models import Max
from xhtml2pdf import pisa
from io import BytesIO
from django.db import transaction
from django.http import StreamingHttpResponse
import time
import requests
import json
import base64
from django.template.loader import get_template
from collections import defaultdict
from datetime import datetime,date,timedelta
from .sqlcommands import * 
from .sqlparams import *
from .forms import *    
from .tasks import *


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

@csrf_exempt
def cancelSchedule(request):
   
    cancelSched = cancelledScheduleParams()

    cancelSched["schedId"] = request.POST.get("schedId", "")
    cancelSched["cancelledDate"] = request.POST.get("cancelDate", "")
    cancelSched["cancelReason"] = request.POST.get("cancelReason", "")
    cancelSched["cancelledBy"] = ""

   
    try:
        sql_query = saveUpdateQueryCancelledSchedule()
        params = (
            cancelSched["schedId"],
            cancelSched["cancelledDate"],
            cancelSched["cancelReason"],
            cancelSched["cancelledBy"] 
        )

        with connection.cursor() as cursor:
            cursor.execute(sql_query, params)

        return JsonResponse({"Status": "Saved"})
    except Exception as err:
        return JsonResponse({"Status": "Error", "Message": str(err)})
 

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

            print("LocationId:", locationId)

            # Save main location
            sql_query = saveUpdateQueryLocation()
            params = (locationId, locName, address, isActive)
            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)

                print(cursor.execute(sql_query, params))
            
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
            print("Error in saveLocation:", str(err))
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
        users = json.loads(users_raw)

        # ✅ Keep only users with "USER STATUS" == "Active"
        active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
        # active_users = [
        #             u for u in users
        #             if u.get("USER_STATUS") == "Active" and u.get("CAMPUS_ID") == 1
        #         ]
        
        return JsonResponse({
            "status": "success",
            "count": len(active_users),
            "usep_users": active_users
        }, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

# def evaluatePunchLogs(request):
#     # 1. Fetch active employees from HRIS
#     try:
#         user_api = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
#         response = requests.get(user_api)
#         response.raise_for_status()
#         users_raw = response.json().get("data", "[]")
#         users = json.loads(users_raw)
#         active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": f"User API error: {str(e)}"})

#     if not active_users:
#         return JsonResponse({"status": "error", "message": "No active users found."})

#     print("❌ Deleting all previous evaluated logs...")
#     EvaluatedPunchLog.objects.all().delete()

#     if EvaluatedPunchLog.objects.count() == 0:
#         with connection.cursor() as cursor:
#             cursor.execute("ALTER TABLE punch_log_eval AUTO_INCREMENT = 1;")
#             print("✅ Auto-increment reset.")

#     punchdates = PunchLog.objects.values_list("punchdate", flat=True).distinct()
#     total_records = 0
#     progress_logs = []

#     def normalize_time_str(t):
#         return t if len(t.split(":")) == 3 else t + ":00"

#     for punchdate in punchdates:
#         print(f"🟡 Evaluating logs for: {punchdate}")
#         month = punchdate.month
#         year = punchdate.year

#         # 🔁 Fetch leave data from API
#         try:
#             leave_response = requests.post(
#                 "https://hris.usep.edu.ph/api/dashboard/view-employee-leave?token=496871859d96697ba10536775445fd8f",
#                 data={"month": month, "year": year}
#             )
#             leave_response.raise_for_status()
#             leave_data = leave_response.json().get("data", [])
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": f"Leave API error: {str(e)}"})

#         # 📌 Build leave map keyed by pds_users_id
#         leave_map = defaultdict(lambda: defaultdict(set))
#         for entry in leave_data:
#             uid = entry.get("pds_users_id")
#             for leave_type, field in [("FL", "force_leave_dates"), ("SL", "sick_leave_dates"), ("VL", "vacation_leave_dates")]:
#                 dates_str = entry.get(field, "")
#                 if dates_str:
#                     for d in dates_str.split(","):
#                         try:
#                             dt = datetime.strptime(d.strip(), "%b-%d-%Y").date()
#                             leave_map[uid][leave_type].add(dt)
#                         except:
#                             continue

#         # ✏️ Get logs and eventNos for punchdate
#         event_nos = PunchLog.objects.filter(punchdate=punchdate).values_list("eventNo", flat=True).distinct()
#         with connection.cursor() as cursor:
#             cursor.execute("""
                # SELECT punchNo, empId, pdsId, employee, eventNo, punchdate,
                #        punchTimeIn, punchTimeOut, latitude, longitude,
                #        officeId, office, systemDateTime
                # FROM punch_log
#                 WHERE punchdate = %s AND isActive = 'Y'
#             """, [punchdate])
#             rows = cursor.fetchall()

#         log_map = {
#             (str(row[2]), str(row[4])): {
#                 "punchNo": str(row[0]),
#                 "empId": str(row[1]),
#                 "pdsId": str(row[2]),
#                 "employee": row[3],
#                 "eventNo": str(row[4]),
#                 "punchdate": row[5],
#                 "punchTimeIn": row[6],
#                 "punchTimeOut": row[7],
#                 "latitude": row[8],
#                 "longitude": row[9],
#                 "officeId": str(row[10]),
#                 "office": row[11],
#                 "systemDateTime": row[12],
#             } for row in rows
#         }

#         # ❌ Check cancelled schedules for this punchdate
#         cancelled_event_map = {}
#         cancelled_scheds = CancelledSchedule.objects.filter(cancelledDate=punchdate)
#         for c_sched in cancelled_scheds:
#             try:
#                 sched = ManSchedule.objects.get(schedId=c_sched.schedId)
#                 event_no = str(sched.eventNo)
#                 start_time = datetime.strptime(normalize_time_str(sched.startTime), "%H:%M:%S").time()
#                 is_morning = start_time < datetime.strptime("12:00:00", "%H:%M:%S").time()
#                 cancelled_event_map[event_no] = {
#                     "cancel_in": is_morning,
#                     "cancel_out": not is_morning
#                 }
#             except ManSchedule.DoesNotExist:
#                 continue

#         evaluated_records = []

#         for emp in active_users:
#             emp_id = str(emp.get("id"))
#             emp_name = emp.get("NAME").strip()
#             empStatus = emp.get("EMPLOYMENT_STATUS")
#             empType = emp.get("EMPLOYMENT_TYPE")
#             empRank = emp.get("EMPLOYMENT_RANK")
#             office_id = str(emp.get("DEPARTMENT_ID"))
#             office = emp.get("DEPARTMENT")
#             campusId = emp.get("CAMPUS_ID")
#             campus = emp.get("CAMPUS")

#             for event_no in event_nos:
#                 key = (emp_id, str(event_no))

#                 # ✅ Check leave status by emp_id
#                 leave_type = None
#                 for lt in ("FL", "SL", "VL"):
#                     if punchdate in leave_map.get(int(emp_id), {}).get(lt, set()):
#                         leave_type = lt
#                         break

#                 if leave_type:
#                     # progress_logs.append(f"🟡 Leave ({leave_type}): {emp_name} [{event_no}]")
#                     yield {"type": "log", "message": f"🟡 Leave ({leave_type}): {emp_name} [{event_no}]"}
#                     record = EvaluatedPunchLog(
#                         punchNo='n/a',
#                         empId=emp_id,
#                         pdsId=emp_id,
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn=leave_type,
#                         punchTimeOut=leave_type,
#                         latitude="0.0",
#                         longitude="0.0",
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="4",
#                         remarks=leave_type
#                     )
#                     evaluated_records.append(record)
#                     continue

#                 # ❌ Check if event is cancelled
#                 cancel_info = cancelled_event_map.get(str(event_no))
#                 if cancel_info:
#                     punch_in_val = "cancelled" if cancel_info["cancel_in"] else "00:00:00"
#                     punch_out_val = "cancelled" if cancel_info["cancel_out"] else "00:00:00"
#                     # progress_logs.append(f"🚫 Cancelled: {emp_name} [{event_no}]")
#                     yield {"type": "log", "message": f"🚫 Cancelled: {emp_name} [{event_no}]"}

#                     record = EvaluatedPunchLog(
#                         punchNo='n/a',
#                         empId=emp_id,
#                         pdsId=emp_id,
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn=punch_in_val,
#                         punchTimeOut=punch_out_val,
#                         latitude="0.0",
#                         longitude="0.0",
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="3",
#                         remarks="Schedule cancelled."
#                     )
#                     evaluated_records.append(record)
#                     continue

#                 # ✅ Present
#                 if key in log_map:
#                     punch = log_map[key]
#                     # progress_logs.append(f"✅ Present: {emp_name} [{event_no}]")
#                     yield {"type": "log", "message": f"✅ Present: {emp_name} [{event_no}]"}
#                     record = EvaluatedPunchLog(
#                         punchNo=punch["punchNo"],
#                         empId=emp_id,
#                         pdsId=punch["pdsId"],
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn=punch["punchTimeIn"],
#                         punchTimeOut=punch["punchTimeOut"],
#                         latitude=punch["latitude"],
#                         longitude=punch["longitude"],
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="1",
#                         remarks="",
#                         systemDateTime=punch["systemDateTime"]
#                     )
#                 else:
#                     # ❌ Absent
#                     # progress_logs.append(f"❌ Absent: {emp_name} [{event_no}]")
#                     yield {"type": "log", "message": f"❌ Absent: {emp_name} [{event_no}]"}
#                     record = EvaluatedPunchLog(
#                         punchNo='n/a',
#                         empId=emp_id,
#                         pdsId=emp_id,
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn="00:00:00",
#                         punchTimeOut="00:00:00",
#                         latitude="0.0",
#                         longitude="0.0",
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="2",
#                         remarks=""
#                     )

#                 evaluated_records.append(record)

#         EvaluatedPunchLog.objects.bulk_create(evaluated_records, batch_size=500)
#         total_records += len(evaluated_records)
#         yield {"type": "done", "message": f"✅ Finished evaluating {total_records} logs."}

#     return JsonResponse({
#         "status": "success",
#         "message": f"{total_records} records evaluated.",
#         "logs": progress_logs,
#         "date": "all"
#     })

# def evaluatePunchLogs(request):
#     from django.db.models import Max
#     from collections import defaultdict
#     from datetime import datetime

#     try:
#         api_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
#         response = requests.get(api_url)
#         response.raise_for_status()
#         users_raw = response.json().get("data", "[]")
#         users = json.loads(users_raw)
#         active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": f"API error: {str(e)}"})

#     if not active_users:
#         return JsonResponse({"status": "error", "message": "No active users found."})

#     # Get last evaluated punchdate from SysPunchStatus
#     punch_status, _ = SysPunchStatus.objects.get_or_create(
#         punchName='punch_log_eval',
#         defaults={'punchCount': '0', 'punchLastPkey': '', 'punchLastDate': None, 'isActive': 'Y'}
#     )
#     last_eval_date = punch_status.punchLastDate

#     # Get all punchdates greater than last evaluated
#     if last_eval_date:
#         punchdates = PunchLog.objects.filter(
#             punchdate__gt=last_eval_date
#         ).values_list("punchdate", flat=True).distinct().order_by("punchdate")
#     else:
#         punchdates = PunchLog.objects.values_list("punchdate", flat=True).distinct().order_by("punchdate")

 
#     # Collect all months/years needed for leave API calls
#     months_years = set((d.month, d.year) for d in punchdates)
#     all_leave_data = []
#     for month, year in months_years:
#         try:
#             leave_response = requests.post(
#                 "https://hris.usep.edu.ph/api/dashboard/view-employee-leave?token=496871859d96697ba10536775445fd8f",
#                 data={"month": month, "year": year}
#             )
#             leave_response.raise_for_status()
#             leave_data = leave_response.json().get("data", [])
#             all_leave_data.extend(leave_data)
#         except Exception:
#             continue

#     # Build leave map: {pds_users_id: {"FL": set(dates), "SL": set(dates), "VL": set(dates)}}
#     leave_map = defaultdict(lambda: defaultdict(set))
#     for entry in all_leave_data:
#         uid = str(entry.get("pds_users_id"))
#         for leave_type, field in [("FL", "force_leave_dates"), ("SL", "sick_leave_dates"), ("VL", "vacation_leave_dates")]:
#             dates_str = entry.get(field, "")
#             if dates_str:
#                 for d in dates_str.split(","):
#                     try:
#                         dt = datetime.strptime(d.strip(), "%b-%d-%Y").date()
#                         leave_map[uid][leave_type].add(dt)
#                     except Exception:
#                         continue

#     total_records = 0
#     progress_logs = []
#     latest_processed_date = last_eval_date

#     for punchdate in punchdates:
#         event_nos = PunchLog.objects.filter(punchdate=punchdate).values_list("eventNo", flat=True).distinct()
#         # Fetch cancelled events for this date
#         cancelled_events = set(
#             ManSchedule.objects.filter(
#                 schedId__in=CancelledSchedule.objects.filter(cancelledDate=punchdate).values_list('schedId', flat=True)
#             ).values_list('eventNo', flat=True)
#         )
#         # Map eventNo to ManSchedule for time reference
#         schedule_map = {
#             str(s.eventNo): s for s in ManSchedule.objects.filter(eventNo__in=event_nos)
#         }

#         # Use raw SQL to fetch punch logs (including systemDateTime)
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT punchNo, empId, pdsId, employee, eventNo, punchdate,
#                     punchTimeIn, punchTimeOut, latitude, longitude,
#                     officeId, office, systemDateTime
#                 FROM punch_log
#                 WHERE punchdate = %s AND isActive = 'Y'
#             """, [punchdate])
#             punch_logs_raw = cursor.fetchall()

#         log_map = {
#             (str(row[2]), str(row[4])): row for row in punch_logs_raw
#         }

#         evaluated_records = []

#         for emp in active_users:
#             emp_id = str(emp.get("id"))
#             emp_name = emp.get("NAME")
#             empStatus = emp.get("EMPLOYMENT_STATUS")
#             empType = emp.get("EMPLOYMENT_TYPE")
#             empRank = emp.get("EMPLOYMENT_RANK")
#             office_id = str(emp.get("DEPARTMENT_ID"))
#             office = emp.get("DEPARTMENT")
#             campusId = emp.get("CAMPUS_ID")
#             campus = emp.get("CAMPUS")

#             for event_no in event_nos:
#                 key = (emp_id, str(event_no))
#                 is_cancelled = str(event_no) in cancelled_events
#                 sched = schedule_map.get(str(event_no))

#                 # --- LEAVE CHECK ---
#                 leave_type = None
#                 for lt in ("FL", "SL", "VL"):
#                     if punchdate in leave_map.get(emp_id, {}).get(lt, set()):
#                         leave_type = lt
#                         break

#                 if leave_type:
#                     record = EvaluatedPunchLog(
#                         punchNo='n/a',
#                         empId=emp_id,
#                         pdsId=emp_id,
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn=leave_type,
#                         punchTimeOut=leave_type,
#                         latitude="0.0",
#                         longitude="0.0",
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="4",
#                         remarks=leave_type,
#                         systemDateTime=None
#                     )
#                 elif key in log_map:
#                     row = log_map[key]
#                     record = EvaluatedPunchLog(
#                         punchNo=row[0],
#                         empId=emp_id,
#                         pdsId=row[2],
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=row[5],
#                         punchTimeIn=row[6],
#                         punchTimeOut=row[7],
#                         latitude=row[8],
#                         longitude=row[9],
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId="1",
#                         remarks="",
#                         systemDateTime=row[12]
#                     )
#                 else:
#                     punch_in = "Absent"
#                     punch_out = "Absent"
#                     att_status = "2"
#                     remarks = ""

#                     if is_cancelled and sched:
#                         if sched.startTime and sched.startTime != "00:00:00":
#                             punch_in = "cancelled"
#                         if sched.endTime and sched.endTime != "00:00:00":
#                             punch_out = "cancelled"
#                         att_status = "3"
#                         remarks = "Schedule cancelled."

#                     record = EvaluatedPunchLog(
#                         punchNo='n/a',
#                         empId=emp_id,
#                         pdsId=emp_id,
#                         employee=emp_name,
#                         empStatus=empStatus,
#                         empType=empType,
#                         empRank=empRank,
#                         eventNo=event_no,
#                         punchdate=punchdate,
#                         punchTimeIn=punch_in,
#                         punchTimeOut=punch_out,
#                         latitude="0.0",
#                         longitude="0.0",
#                         officeId=office_id,
#                         office=office,
#                         campusId=campusId,
#                         campus=campus,
#                         isActive='Y',
#                         attStatusId=att_status,
#                         remarks=remarks,
#                         systemDateTime=None
#                     )
#                 evaluated_records.append(record)

#         EvaluatedPunchLog.objects.bulk_create(evaluated_records, batch_size=500)
#         total_records += len(evaluated_records)
#         latest_processed_date = punchdate

#     # Update SysPunchStatus with new last punchdate and count
#     if latest_processed_date:
#         punch_status.punchLastPkey = ""
#         punch_status.punchLastDate = latest_processed_date
#         punch_status.punchCount = str(EvaluatedPunchLog.objects.count())
#         punch_status.save()

#     return JsonResponse({
#         "status": "success",
#         "message": f"{total_records} new records evaluated.",
#         "logs": progress_logs,
#         "date": "incremental"
#     })

# def evaluatePunchLogs(request):
#     from django.db.models import Max
#     from collections import defaultdict
#     from datetime import datetime

#     def sse_stream():
#         try:
#             api_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
#             response = requests.get(api_url)
#             response.raise_for_status()
#             users_raw = response.json().get("data", "[]")
#             users = json.loads(users_raw)
#             active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
#         except Exception as e:
#             yield f"data: {json.dumps({'message': f'API error: {str(e)}'})}\n\n"
#             return

#         if not active_users:
#             yield f"data: {json.dumps({'message': 'No active users found.'})}\n\n"
#             return

#         punch_status, _ = SysPunchStatus.objects.get_or_create(
#             punchName='punch_log_eval',
#             defaults={'punchCount': '0', 'punchLastPkey': '', 'punchLastDate': None, 'isActive': 'Y'}
#         )
#         last_eval_date = punch_status.punchLastDate

#         if last_eval_date:
#             punchdates = PunchLog.objects.filter(
#                 punchdate__gt=last_eval_date
#             ).values_list("punchdate", flat=True).distinct().order_by("punchdate")
#         else:
#             punchdates = PunchLog.objects.values_list("punchdate", flat=True).distinct().order_by("punchdate")

#         months_years = set((d.month, d.year) for d in punchdates)
#         all_leave_data = []
#         for month, year in months_years:
#             try:
#                 leave_response = requests.post(
#                     "https://hris.usep.edu.ph/api/dashboard/view-employee-leave?token=496871859d96697ba10536775445fd8f",
#                     data={"month": month, "year": year}
#                 )
#                 leave_response.raise_for_status()
#                 leave_data = leave_response.json().get("data", [])
#                 all_leave_data.extend(leave_data)
#             except Exception:
#                 continue

#         leave_map = defaultdict(lambda: defaultdict(set))
#         for entry in all_leave_data:
#             uid = str(entry.get("pds_users_id"))
#             for leave_type, field in [("FL", "force_leave_dates"), ("SL", "sick_leave_dates"), ("VL", "vacation_leave_dates")]:
#                 dates_str = entry.get(field, "")
#                 if dates_str:
#                     for d in dates_str.split(","):
#                         try:
#                             dt = datetime.strptime(d.strip(), "%b-%d-%Y").date()
#                             leave_map[uid][leave_type].add(dt)
#                         except Exception:
#                             continue
        
                            

#         total_records = 0
#         latest_processed_date = last_eval_date
#         punchdate_count = len(punchdates)
#         punchdate_idx = 0



#         for punchdate in punchdates:
#             punchdate_idx += 1
#             yield f"data: {json.dumps({'message': f'Processing {punchdate} ({punchdate_idx}/{punchdate_count})'})}\n\n"
#             event_nos = PunchLog.objects.filter(punchdate=punchdate).values_list("eventNo", flat=True).distinct()
#             cancelled_events = set(
#                 ManSchedule.objects.filter(
#                     schedId__in=CancelledSchedule.objects.filter(cancelledDate=punchdate).values_list('schedId', flat=True)
#                 ).values_list('eventNo', flat=True)
#             )
#             schedule_map = {
#                 str(s.eventNo): s for s in ManSchedule.objects.filter(eventNo__in=event_nos)
#             }

#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                     SELECT punchNo, empId, pdsId, employee, eventNo, punchdate,
#                         punchTimeIn, punchTimeOut, latitude, longitude,
#                         officeId, office, systemDateTime
#                     FROM punch_log
#                     WHERE punchdate = %s AND isActive = 'Y'
#                 """, [punchdate])
#                 punch_logs_raw = cursor.fetchall()

#             log_map = {
#                 (str(row[2]), str(row[4])): row for row in punch_logs_raw
#             }

#             evaluated_records = []

#             for emp in active_users:
#                 emp_id = str(emp.get("id"))
#                 emp_name = emp.get("NAME")
#                 empStatus = emp.get("EMPLOYMENT_STATUS")
#                 empType = emp.get("EMPLOYMENT_TYPE")
#                 empRank = emp.get("EMPLOYMENT_RANK")
#                 office_id = str(emp.get("DEPARTMENT_ID"))
#                 office = emp.get("DEPARTMENT")
#                 campusId = emp.get("CAMPUS_ID")
#                 campus = emp.get("CAMPUS")

#                 for event_no in event_nos:
#                     key = (emp_id, str(event_no))
#                     is_cancelled = str(event_no) in cancelled_events
#                     sched = schedule_map.get(str(event_no))

#                     # --- LEAVE CHECK ---
#                     leave_type = None
#                     for lt in ("FL", "SL", "VL"):
#                         if punchdate in leave_map.get(emp_id, {}).get(lt, set()):
#                             leave_type = lt
#                             break

#                     if leave_type:
#                         msg = f"🟡 Leave ({leave_type}): {emp_name} [{event_no}]"
#                         record = EvaluatedPunchLog(
#                             punchNo='n/a',
#                             empId=emp_id,
#                             pdsId=emp_id,
#                             employee=emp_name,
#                             empStatus=empStatus,
#                             empType=empType,
#                             empRank=empRank,
#                             eventNo=event_no,
#                             punchdate=punchdate,
#                             punchTimeIn=leave_type,
#                             punchTimeOut=leave_type,
#                             latitude="0.0",
#                             longitude="0.0",
#                             officeId=office_id,
#                             office=office,
#                             campusId=campusId,
#                             campus=campus,
#                             isActive='Y',
#                             attStatusId="4",
#                             remarks=leave_type,
#                             systemDateTime=None
#                         )
#                     elif key in log_map:
#                         row = log_map[key]
#                         msg = f"✅ Present: {emp_name} [{event_no}]"
#                         record = EvaluatedPunchLog(
#                             punchNo=row[0],
#                             empId=emp_id,
#                             pdsId=row[2],
#                             employee=emp_name,
#                             empStatus=empStatus,
#                             empType=empType,
#                             empRank=empRank,
#                             eventNo=event_no,
#                             punchdate=row[5],
#                             punchTimeIn=row[6],
#                             punchTimeOut=row[7],
#                             latitude=row[8],
#                             longitude=row[9],
#                             officeId=office_id,
#                             office=office,
#                             campusId=campusId,
#                             campus=campus,
#                             isActive='Y',
#                             attStatusId="1",
#                             remarks="",
#                             systemDateTime=row[12]
#                         )
#                     else:
#                         punch_in = "Absent"
#                         punch_out = "Absent"
#                         att_status = "2"
#                         remarks = ""
#                         if is_cancelled and sched:
#                             if sched.startTime and sched.startTime != "00:00:00":
#                                 punch_in = "cancelled"
#                             if sched.endTime and sched.endTime != "00:00:00":
#                                 punch_out = "cancelled"
#                             att_status = "3"
#                             remarks = "Schedule cancelled."
#                         msg = f"❌ Absent: {emp_name} [{event_no}]" if not is_cancelled else f"🚫 Cancelled: {emp_name} [{event_no}]"
#                         record = EvaluatedPunchLog(
#                             punchNo='n/a',
#                             empId=emp_id,
#                             pdsId=emp_id,
#                             employee=emp_name,
#                             empStatus=empStatus,
#                             empType=empType,
#                             empRank=empRank,
#                             eventNo=event_no,
#                             punchdate=punchdate,
#                             punchTimeIn=punch_in,
#                             punchTimeOut=punch_out,
#                             latitude="0.0",
#                             longitude="0.0",
#                             officeId=office_id,
#                             office=office,
#                             campusId=campusId,
#                             campus=campus,
#                             isActive='Y',
#                             attStatusId=att_status,
#                             remarks=remarks,
#                             systemDateTime=None
#                         )
#                     evaluated_records.append(record)
#                     yield f"data: {json.dumps({'message': msg})}\n\n"

#             EvaluatedPunchLog.objects.bulk_create(evaluated_records, batch_size=500)
#             total_records += len(evaluated_records)
#             latest_processed_date = punchdate
#             yield f"data: {json.dumps({'message': f'✅ Finished {punchdate} ({punchdate_idx}/{punchdate_count})'})}\n\n"

#         # Update SysPunchStatus
#         if latest_processed_date:
#             punch_status.punchLastPkey = ""
#             punch_status.punchLastDate = latest_processed_date
#             punch_status.punchCount = str(EvaluatedPunchLog.objects.count())
#             punch_status.save()

#         yield f"event: close\ndata: {json.dumps({'message': f'✅ Evaluation complete. {total_records} records evaluated.'})}\n\n"

#     return StreamingHttpResponse(sse_stream(), content_type='text/event-stream')
def evaluatePunchLogs(request):
    def sse_stream():
        # tolerance for matching manual entries to punch times
        tolerance = timedelta(minutes=5)

        # --- 1) Fetch active users ---
        try:
            api_url = "https://hris.usep.edu.ph/api/dashboard/view-users?token=496871859d96697ba10536775445fd8f"
            response = requests.get(api_url)
            response.raise_for_status()
            users_raw = response.json().get("data", "[]")
            users = json.loads(users_raw)
            active_users = [user for user in users if user.get("USER_STATUS") == "Active"]
        except Exception as e:
            yield f"data: {json.dumps({'message': f'API error (users): {str(e)}'})}\n\n"
            return

        if not active_users:
            yield f"data: {json.dumps({'message': 'No active users found.'})}\n\n"
            return

        # --- 2) Determine punchdates (must do this BEFORE fetching manual entries) ---
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

        # --- 3) Fetch manual entries for each unique (year, month) in punchdates ---
        manual_entries_url = "https://hris.usep.edu.ph/api/dashboard/view-manual-entries"
        manual_map = defaultdict(list)  # key: date -> list of {userid, datetime, justification}
        unique_periods = {(d.year, d.month) for d in punchdates}

        for year, month in unique_periods:
            try:
                me_response = requests.post(
                    manual_entries_url,
                    data={
                        "month": month,
                        "year": year,
                        "token": "496871859d96697ba10536775445fd8f"
                    }
                )
                me_response.raise_for_status()
                manual_entries = me_response.json().get("data", [])
                for me in manual_entries:
                    try:
                        me_dt = datetime.strptime(me["datetime"], "%Y-%m-%d %H:%M:%S")
                        manual_map[me_dt.date()].append({
                            "userid": str(me["userid"]),
                            "datetime": me_dt,
                            "justification": me.get("justification", "")
                        })
                    except Exception:
                        # skip malformed manual entry datetime
                        continue
            except Exception as e:
                yield f"data: {json.dumps({'message': f'Manual Entry API error for {month}/{year}: {str(e)}'})}\n\n"
                # continue to next period

        # --- 4) Fetch leave data per month/year (existing logic) ---
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

        # helper to safely parse time-like field into a datetime (or None).
        def _parse_time_field_to_dt(field_value, punchdate):
            """
            field_value: could be None, 'ME', a time string 'HH:MM:SS', a time object, or something else.
            Returns datetime (punchdate + time) or None.
            """
            if not field_value:
                return None
            s = str(field_value).strip()
            if not s:
                return None
            if s.upper() == "ME":
                return None
            # If value contains space, take last token (handles 'YYYY-MM-DD HH:MM:SS' or similar)
            if " " in s:
                s = s.split(" ")[-1]
            try:
                t = datetime.strptime(s, "%H:%M:%S").time()
                return datetime.combine(punchdate, t)
            except Exception:
                # give up, return None
                return None

        # --- 5) Main evaluation loop (preserve your original logic) ---
        total_records = 0
        latest_processed_date = last_eval_date
        punchdate_count = len(punchdates)
        punchdate_idx = 0

        for punchdate in punchdates:
            punchdate_idx += 1
            yield f"data: {json.dumps({'message': f'Processing {punchdate} ({punchdate_idx}/{punchdate_count})'})}\n\n"

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

            # map by (pdsId, eventNo) as before
            log_map = {
                (str(row[2]), str(row[4])): row for row in punch_logs_raw
            }

            evaluated_records = []
            me_for_date = manual_map.get(punchdate, [])

            for emp in active_users:
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
                        # Leave record
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
                        # Present: check manual entry proximity (ME) before creating evaluated record
                        row = list(log_map[key])  # copy so we can mutate row[6]/row[7] safely in-memory
                        justification = ""

                        # safe parse the original punch times to datetimes for comparison
                        punch_in_dt = _parse_time_field_to_dt(row[6], punchdate)
                        punch_out_dt = _parse_time_field_to_dt(row[7], punchdate)

                        # Check manual entries for that user on this date
                        for me in me_for_date:
                            if me["userid"] == emp_id:
                                me_dt = me["datetime"]
                                # match against punch in/out with tolerance
                                if punch_in_dt and abs(me_dt - punch_in_dt) <= tolerance:
                                    row[6] = "ME"
                                    justification = me.get("justification", "") or justification
                                if punch_out_dt and abs(me_dt - punch_out_dt) <= tolerance:
                                    row[7] = "ME"
                                    justification = me.get("justification", "") or justification
                                # If punch_in/punch_out were None but you want to mark ME even if DB had no in/out,
                                # you could add logic here to set row[6]/row[7] = "ME" when punch_in_dt is None.
                                # (Currently we only tag existing times within tolerance.)

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
                            remarks=justification,
                            systemDateTime=row[12]
                        )

                    else:
                        # Absent or Cancelled
                        punch_in = "Absent"
                        punch_out = "Absent"
                        att_status = "2"
                        remarks = ""
                        if is_cancelled and sched:
                            if getattr(sched, "startTime", None) and sched.startTime != "00:00:00":
                                punch_in = "cancelled"
                            if getattr(sched, "endTime", None) and sched.endTime != "00:00:00":
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
                    yield f"data: {json.dumps({'message': msg})}\n\n"

            # bulk insert for this date
            if evaluated_records:
                EvaluatedPunchLog.objects.bulk_create(evaluated_records, batch_size=500)
                total_records += len(evaluated_records)

            latest_processed_date = punchdate
            yield f"data: {json.dumps({'message': f'✅ Finished {punchdate} ({punchdate_idx}/{punchdate_count})'})}\n\n"

        # --- Update SysPunchStatus as before ---
        if latest_processed_date:
            punch_status.punchLastPkey = ""
            punch_status.punchLastDate = latest_processed_date
            punch_status.punchCount = str(EvaluatedPunchLog.objects.count())
            punch_status.save()

        # Signal close
        yield f"event: close\ndata: {json.dumps({'message': f'✅ Evaluation complete. {total_records} records evaluated.'})}\n\n"

    return StreamingHttpResponse(sse_stream(), content_type='text/event-stream')
def attJsonListEvalLogs(request):
    start_date = request.GET.get("startdate")
    end_date = request.GET.get("enddate")
    campus = request.GET.get("campusid")
    office = request.GET.get("office")
    attstatusid = request.GET.get("attstatusid")
    event_no = request.GET.get("event")

    groupby = request.GET.get("groupby", "eventdate")  # default is eventdate

    filterQuery = ""
    params = []

    # Date range filter
    if start_date and end_date:
        filterQuery += " AND eval.punchDate BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    
    #Campus filter
    if campus:
        filterQuery += " AND eval.campusId = %s"
        params.append(campus)

    #event filter
    if event_no and event_no != "all":
        filterQuery += " AND eval.eventNo = %s"
        params.append(event_no)

    # Office filter
    if office:
        filterQuery += " AND eval.officeId = %s"
        params.append(office)

    # Attendance status filter
    if attstatusid:
        filterQuery += " AND eval.attStatusId = %s"
        params.append(attstatusid)

    # Execute query
    with connection.cursor() as cursor:
        cursor.execute(fetchEvalPunchLogs(filterQuery), params)
        rows = cursor.fetchall()

    # No grouping: flat list
    if groupby == "none":
        flat_logs = []
        for row in rows:
            flat_logs.append({
              "evalPunchNo": row[0],
                "punchNo": row[1],
                "eventName": row[2],
                "empId": row[3],
                "pdsId": row[4],
                "employee": row[5],
                "empStatus": row[6],
                "empType": row[7],
                "empRank": row[8],
                "punchDate": row[9],
                "punchTimeIn": row[10],
                "punchTimeOut": row[11],
                "latitude": row[12],
                "longitude": row[13],
                "officeId": row[14],
                "office": row[15],
                "campusId": row[16],
                "campus": row[17],
                "systemDateTime": row[18],
                "attStatusId": row[19],
                "isActive": row[20],
            })
        return JsonResponse(flat_logs, safe=False)

    # Grouped by event + date -> office -> logs
    grouped_result = {}

    for row in rows:
        event_name = row[2]
        punch_date = row[9]
        office = row[15]

        # Format: "Flag Ceremony (2025-07-15)"
        # group_key = f"{event_name} ({punch_date})"
        formatted_date = punch_date.strftime("%B %d, %Y")
        group_key = f"{event_name} ({formatted_date})"
        log = {
            "evalPunchNo": row[0],
            "punchNo": row[1],
            "empId": row[3],
            "pdsId": row[4],
            "employee": row[5],
            "empStatus": row[6],
            "empType": row[7],
            "empRank": row[8],
            "punchDate": punch_date,
            "punchTimeIn": row[10],
            "punchTimeOut": row[11],
            "latitude": row[12],
            "longitude": row[13],
            "officeId": row[14],
            "office": office,
            "campusId": row[16],
            "campus": row[16],
            "systemDateTime": row[18],
            "attStatusId": row[19],
        }

        # Initialize event group
        if group_key not in grouped_result:
            grouped_result[group_key] = {}

        # Initialize office group
        if office not in grouped_result[group_key]:
            grouped_result[group_key][office] = []

        grouped_result[group_key][office].append(log)

    # Sort keys chronologically based on punchDate inside the key
    sorted_grouped = dict(
        sorted(
            grouped_result.items(),
            key=lambda item: item[0].split("(")[-1].replace(")", "")
        )
    )

    return JsonResponse(sorted_grouped)

# def evaluateRawLogs(request):
#     try:
#         # Get current counts from both tables
#         punch_log_qs = PunchLog.objects.filter(isActive='Y')
#         eval_log_qs = EvaluatedPunchLog.objects.filter(isActive='Y')
#         punch_log_count = punch_log_qs.count()
#         eval_log_count = eval_log_qs.count()

#         # Initialize sys_punch records if they don't exist
#         punch_log_row, _ = SysPunchStatus.objects.get_or_create(
#             punchName='punch_log',
#             defaults={
#                 'punchCount': str(punch_log_count),
#                 'punchLastPkey': '',
#                 'isActive': 'Y'
#             }
#         )

#         eval_log_row, _ = SysPunchStatus.objects.get_or_create(
#             punchName='punch_log_eval',
#             defaults={
#                 'punchCount': str(eval_log_count),
#                 'punchLastPkey': '',
#                 'isActive': 'Y'
#             }
#         )

#         # Convert stored counts for comparison
#         stored_punch_log = int(punch_log_row.punchCount)
#         stored_eval_log = int(eval_log_row.punchCount)

#         # Determine latest primary keys
#         latest_punch_log_pkey = str(punch_log_qs.order_by('-punchNo').first().punchNo) if punch_log_count > 0 else ''
#         latest_eval_log_pkey = str(eval_log_qs.order_by('-evalPunchNo').first().evalPunchNo) if eval_log_count > 0 else ''

#         # Update stored status with current counts and last primary keys
#         punch_log_row.punchCount = str(punch_log_count)
#         punch_log_row.punchLastPkey = latest_punch_log_pkey
#         punch_log_row.save()

#         eval_log_row.punchCount = str(eval_log_count)
#         eval_log_row.punchLastPkey = latest_eval_log_pkey
#         eval_log_row.save()

#         # Compare and generate evaluation status
#         messages = []
#         needs_eval = False

#         if punch_log_count > stored_punch_log:
#             messages.append("🟡 New entries detected in punch_log.")
#             needs_eval = True

#         if eval_log_count < stored_eval_log:
#             messages.append("⚠️ Evaluated logs are inconsistent.")
#             needs_eval = True

#         if needs_eval:
#             return JsonResponse({
#                 "status": "pending",
#                 "message": " ".join(messages),
#                 "newPunchLogEntries": punch_log_count - stored_punch_log,
#                 "storedPunchCount": stored_punch_log,
#                 "currentPunchCount": punch_log_count,
#                 "evalLogCount": eval_log_count,
#                 "lastPunchPkey": latest_punch_log_pkey,
#                 "lastEvalPkey": latest_eval_log_pkey
#             })

#         return JsonResponse({
#             "status": "ok",
#             "message": "✅ Logs are up to date.",
#             "newPunchLogEntries": 0,
#             "storedPunchCount": stored_punch_log,
#             "currentPunchCount": punch_log_count,
#             "evalLogCount": eval_log_count,
#             "lastPunchPkey": latest_punch_log_pkey,
#             "lastEvalPkey": latest_eval_log_pkey
#         })

#     except Exception as e:
#         return JsonResponse({
#             "status": "error",
#             "message": f"An error occurred: {str(e)}"
#         })
def evaluateRawLogs(request):
    try:
        # 1. Fetch all logs
        punch_log_qs = PunchLog.objects.filter(isActive='Y')
        eval_log_qs = EvaluatedPunchLog.objects.filter(isActive='Y')

        punch_log_count = punch_log_qs.count()
        eval_log_count = eval_log_qs.count()

        # 2. Get or create sys_punch rows for tracking
        punch_log_status, _ = SysPunchStatus.objects.get_or_create(
            punchName='punch_log',
            defaults={'punchCount': '0', 'punchLastPkey': '', 'isActive': 'Y'}
        )
        eval_log_status, _ = SysPunchStatus.objects.get_or_create(
            punchName='punch_log_eval',
            defaults={'punchCount': '0', 'punchLastPkey': '', 'isActive': 'Y'}
        )

        # 3. Convert stored counts to int for comparison
        stored_punch_count = int(punch_log_status.punchCount or 0)
        stored_eval_count = int(eval_log_status.punchCount or 0)

        # 4. Determine new punch logs
        if eval_log_count == 0 and punch_log_count > 0:
            new_punch_log_entries = punch_log_count
        else:
            new_punch_log_entries = punch_log_count - stored_punch_count

        new_punch_log_entries = max(0, new_punch_log_entries)  # safety net

        # 5. Determine latest primary keys
        latest_punch_log_pkey = (
            str(punch_log_qs.order_by('-punchNo').first().punchNo)
            if punch_log_count > 0 else ''
        )
        latest_eval_log_pkey = (
            str(eval_log_qs.order_by('-evalPunchNo').first().evalPunchNo)
            if eval_log_count > 0 else ''
        )

        # 6. Update punch status table to reflect current state
        punch_log_status.punchCount = str(punch_log_count)
        punch_log_status.punchLastPkey = latest_punch_log_pkey
        punch_log_status.save()

        eval_log_status.punchCount = str(eval_log_count)
        eval_log_status.punchLastPkey = latest_eval_log_pkey
        eval_log_status.save()

        # 7. Message status
        messages = []
        status = "ok"
        if new_punch_log_entries > 0:
            messages.append("🟡 New entries detected in punch_log.")
            status = "pending"
        if eval_log_count < stored_eval_count:
            messages.append("⚠️ Evaluated logs are inconsistent.")
            status = "inconsistent"

        return JsonResponse({
            "status": status,
            "messages": messages,
            "newPunchLogEntries": new_punch_log_entries,
            "currentPunchCount": punch_log_count,
            "storedPunchCount": stored_punch_count,
            "lastPunchPkey": latest_punch_log_pkey,
            "lastEvalPkey": latest_eval_log_pkey,
            "lastEvalPunchCount":stored_eval_count
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

#Reports

def evalPunchLogView(request):
    # Example event fetch (keep as-is if needed)
    events = ManEvent.objects.raw(fetchQueryEvent())

    # 🔹 Fetch distinct officeId and office name (exclude empty/null)
    offices = (
        EvaluatedPunchLog.objects
        .filter(officeId__isnull=False, office__isnull=False)
        .exclude(officeId__exact="")
        .values('officeId', 'office')
        .distinct()
        .order_by('office')  # Optional: sort alphabetically
    )
    campuses = (
        EvaluatedPunchLog.objects
        .filter(campusId__isnull=False, campus__isnull=False)
        .exclude(campusId__exact="")
        .values('campusId', 'campus')
        .distinct()
        .order_by('campus')
    )

    return render(
        request,
        'amsApp/attendance-eval.html',
        {
            'events': events,
            'offices': offices,  
            'campuses': campuses,
        }
    )

def evalLogStatusJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchSysPunchStatus())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "sysEvalId":row[0],
            "punchName":row[1],
            "punchCount":row[2],
            "isActive":row[3]
           }
        jsonResultData.append(tempRes)
        
    return JsonResponse({"data":list(jsonResultData)},safe=False)
    
#print 
def printView(request):
    # return render(request, 'amsApp/print.html')
   
    encoded_data = request.GET.get("data", "")
    if not encoded_data:
        return HttpResponse("No data provided", status=400)

    try:
        decoded_json = base64.b64decode(encoded_data).decode("utf-8")
        context = json.loads(decoded_json)
    except Exception as e:
        return HttpResponse(f"Error decoding data: {str(e)}", status=400)

    # Load and render the template
    template = get_template("amsApp/print.html")
    html = template.render(context)

    # Create a PDF using xhtml2pdf
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'filename="attendance_{context["date"]}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("PDF generation failed", status=500)

    return response

def printBatchReport(request):
    # 1. Parse query parameters
    start_date_str = request.GET.get("startdate")
    end_date_str = request.GET.get("enddate")
    office = request.GET.get("office")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception:
        return render(request, "amsApp/error.html", {"error": "Invalid date format"})

    # 2. Generate week ranges
    def get_week_ranges(start, end):
        weeks = []
        current = start
        week_num = 1
        while current <= end:
            week_start = current
            week_end = min(week_start + timedelta(days=6), end)
            weeks.append((f"Week {week_num}", week_start, week_end))
            current = week_end + timedelta(days=1)
            week_num += 1
        return weeks

    weeks = get_week_ranges(start_date, end_date)

    # 3. Build WHERE clause
    filters = f"AND eval.punchDate BETWEEN '{start_date}' AND '{end_date}'"
    if office:
        filters += f" AND eval.officeId = '{office}'"

    # 4. SQL query
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT eval.evalPunchNo, eval.punchNo, evt.eventName,
                   eval.empId, eval.employee, eval.empRank,
                   eval.punchDate, eval.punchTimeIn, eval.punchTimeOut,
                   eval.office, eval.attStatusId
            FROM punch_log_eval eval
            LEFT JOIN man_event evt ON eval.eventNo = evt.eventNo
            WHERE eval.isActive = 'Y' {filters}
            ORDER BY eval.employee, eval.punchDate
        """)
        rows = cursor.fetchall()

    # 5. Column mapping
    COLS = {
        'eventName': 2,
        'employee': 4,
        'empRank': 5,
        'punchDate': 6,
        'punchTimeIn': 7,
        'punchTimeOut': 8,
    }

    # 6. Group data
    grouped_data = defaultdict(lambda: {
        "position": "",
        "weeks": defaultdict(dict)
    })

    for row in rows:
        emp_name = row[COLS['employee']]
        position = row[COLS['empRank']]
        date = row[COLS['punchDate']]
        event = row[COLS['eventName']]
        timein = row[COLS['punchTimeIn']]
        timeout = row[COLS['punchTimeOut']]

        # Choose the correct time based on event type
        if "ceremony" in event.lower():
            punch_time = timein
        elif "retreat" in event.lower():
            punch_time = timeout
        else:
            punch_time = timein  # default fallback

        if not punch_time or str(punch_time) == "00:00:00":
            punch_time = "Absent"

        for label, start, end in weeks:
            if start <= date <= end:
                event_key = f"{event} - {date.strftime('%B %d, %Y')}"
                grouped_data[emp_name]["position"] = position
                grouped_data[emp_name]["weeks"][label][event_key] = punch_time
                break

    template_path = 'amsApp/print-batch.html'
    context = {
        "start_date": start_date,
        "end_date": end_date,
        "office": office,
        "weeks": weeks,
        "data": list(grouped_data.items()),  # list of tuples for template iteration
    }
    # Render and convert to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="AttendanceBatchReport.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation failed')
    return response
    # return render(request, "amsApp/print-batch.html", context)

def printBatch(request):
    return render(request, 'amsApp/print-batch.html')

#celery 

def start_evaluation(request):
    task = evaluate_punch_logs_task.delay()
    cache.delete(f"eval_progress_{task.id}")  # clear old progress
    return JsonResponse({"task_id": task.id})

def evaluation_progress(request):
    task_id = request.GET.get("task_id")
    progress = cache.get(f"eval_progress_{task_id}", {"percent": 0, "logs": []})
    return JsonResponse(progress)