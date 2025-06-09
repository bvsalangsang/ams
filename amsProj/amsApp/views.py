from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
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
    locations = ManLocation.objects.raw(fetchQueryLocation())
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
            return request.POST.get(key, default).strip()

        # Assign fields with defaults
        schedule["schedId"] = get_post("schedId")
        schedule["locationId"] = get_post("locationId")
        schedule["eventNo"] = get_post("eventNo")
        schedule["startDate"] = get_post("startDate") or "0000-00-00"
        schedule["endDate"] = get_post("endDate") or "0000-00-00"
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
    return render(request, 'amsApp/map-location.html')