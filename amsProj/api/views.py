from django.db import connection
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.decorators import api_view
from amsApp.models import *
from api.sqlcommands import *
from api.sqlparams import *
from .serializers import *



# Punch log API
@api_view(['GET'])
def getDataPunch(request):
    try:
        punchlog = PunchLog.objects.all()
        punchserializer = PunchSerializer(punchlog, many=True)
        return Response(punchserializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def getPunchByDate(request):
    pdsId = request.GET.get('pdsId')
    punchDate = request.GET.get('punchDate')
   

    if not pdsId or not punchDate:
        return Response({"error": "Missing pdsId or punchDate"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            sql, params = queryGetLogByDate(pdsId=pdsId, punchDate=punchDate)
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                result = dict(zip(columns, row))
                return Response({"data": result}, status=status.HTTP_200_OK)
            else:
                return Response({"data": None}, status=status.HTTP_404_NOT_FOUND)


    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def getPunchByPdsId(request):
    pdsId = request.GET.get('pdsId')
   
    if not pdsId:
        return Response({"error": "Missing pdsId"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            sql, params = queryGetPunchLogByPdsId(pdsId=pdsId)
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        tempRes = None
        jsonResultData = []

        if rows:
            for row in rows:
                tempRes = {
                    "punchNo":row[0],
                    "event":row[1],
                    "empId":row[2],
                    "pdsId":row[3],
                    "employee":row[4],
                    "punchdate":row[5],
                    "punchTimeIn":row[6],
                    "punchTimeOut":row[7],
                    "latitude":row[8],
                    "longitude":row[9],
                    "systemDateTime":row[10]
                }
                jsonResultData.append(tempRes)
            return Response({"data": jsonResultData}, status=status.HTTP_200_OK)
        else:
            return Response({"data": None}, status=status.HTTP_404_NOT_FOUND)


    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def addPunchLog(request):
    serializer = PunchSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Shift API
@api_view(['GET'])
def getDataShift(request):
    try:
        shift = ManShift.objects.all()
        shiftserializer = ShiftSerializer(shift, many=True)
        return Response(shiftserializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# System Info API
@api_view(['GET'])
def getSysInfo(request):
    try:
        appInfo = sysInfo.objects.all()
        appInfoSerializer = SytemInfoSerializer(appInfo, many=True)
        return Response(appInfoSerializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# schedule API
@api_view(['GET'])
def getDataSchedule(request):
    try:
        with connection.cursor() as cursor:
            sql, params = queryGetSchedule()
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        tempRes = None
        jsonResultData = []

        if rows:
            for row in rows:
                tempRes = {
                    "schedId": row[0],
                    "locId": row[1],
                    "locName": row[2],
                    "eventNo": row[3],
                    "eventName": row[4],
                    "startDate": row[5] if row[5] else "0000-00-00",
                    "endDate": row[6] if row[6] else "0000-00-00",
                    "startTime": row[7] if row[7] else "00:00",
                    "startGrace": row[8] if row[8] else "00",
                    "endTime": row[9] if row[9] else "00:00",
                    "endGrace": row[10] if row[10] else "00",
                    "recurrenceType": row[11],
                    "recurrenceDays": row[12],
                    "dateCreated": str(row[13]) if row[13] else None,
                    "isRecurring": row[14],
                    "isSet": row[15],
                    "isActive": row[16],
                }
                jsonResultData.append(tempRes)
            return Response({"data": jsonResultData}, status=status.HTTP_200_OK)
        else:
            return Response({"data": None}, status=status.HTTP_404_NOT_FOUND)


    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def getScheduleByDate(request):
    startDate = request.GET.get('startDate')
    endDate = request.GET.get('endDate')

    if not startDate or not endDate:
        return Response({"error": "Missing startDate or endDate"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            sql, params = queryGetScheduleByDate(startDate=startDate, endDate=endDate)
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        tempRes = None
        jsonResultData = []

        if rows:
            for row in rows:
                tempRes = {
                    "schedId": row[0],
                    "locId": row[1],
                    "locName": row[2],
                    "eventNo": row[3],
                    "eventName": row[4],
                    "startDate": row[5] if row[5] else "0000-00-00",
                    "endDate": row[6] if row[6] else "0000-00-00",
                    "startTime": row[7] if row[7] else "00:00",
                    "startGrace": row[8] if row[8] else "00",
                    "endTime": row[9] if row[9] else "00:00",
                    "endGrace": row[10] if row[10] else "00",
                    "recurrenceType": row[11],
                    "recurrenceDays": row[12],
                    "dateCreated": str(row[13]) if row[13] else None,
                    "isRecurring": row[14],
                    "isSet": row[15],
                    "isActive": row[16],
                }
                jsonResultData.append(tempRes)
            return Response({"data": jsonResultData}, status=status.HTTP_200_OK)
        else:
            return Response({"data": None}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# location API
@api_view(['GET'])
def getLocationById(request):
    locId = request.GET.get('locId')
    
    if not locId:
        return Response({"error": "Missing locId"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            sql, params = queryLocationById(locId=locId)
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        if rows:
            # Assume all rows have the same location info, just different coordinates
            locationId = rows[0][0]
            locName = rows[0][1]
            address = rows[0][2]
            coordinates = []
            for row in rows:
                coordinates.append({
                    "longitude": row[3],
                    "latitude": row[4]
                })
            result = {
                "locationId": locationId,
                "locName": locName,
                "address": address,
                "coordinates": coordinates
            }
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response({"data": None}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)