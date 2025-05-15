from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .sqlcommands import * 
from .sqlparams import *

def dashboard(request):
    return render(request, 'amsApp/dashboard.html')

def attendanceLogs(request):
    return render(request, 'amsApp/attendance-log.html')

def attJsonList(request):
    with connection.cursor() as cursor:
        cursor.execute(fetchAttLogs())
        rows = cursor.fetchall()

    tempRes = None
    jsonResultData = []

    for row in rows:
        tempRes = {
            "punchNo":row[0],
            "shiftNo":row[1],
            "empId":row[2],
            "pdsId":row[3],
            "punchdate":row[4],
            "punchTimeIn":row[5],
            "punchTimeOut":row[6],
            "latitude":row[7],
            "longitude":row[8],
            "systemDateTime":row[9]
           }
        jsonResultData.append(tempRes)
    return JsonResponse({"data":list(jsonResultData)},safe=False)


#shift view
def shiftView(request):
    return render(request, 'amsApp/event.html')

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
