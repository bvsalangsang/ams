from rest_framework.response import Response 
from rest_framework import status
from rest_framework.decorators import api_view
from amsApp.models import *
from .serializers import *

@api_view(['GET'])
def getDataPunch(request):
    try:
        punchlog = PunchLog.objects.all()
        punchserializer = PunchSerializer(punchlog, many=True)
        return Response(punchserializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def getDataShift(request):
    try:
        shift = ManShift.objects.all()
        shiftserializer = ShiftSerializer(shift, many=True)
        return Response(shiftserializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def addPunchLog(request):
    serializer = PunchSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


