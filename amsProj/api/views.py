from rest_framework.response import Response
from rest_framework.decorators import api_view
from amsApp.models import *
from .serializers import *

@api_view(['GET'])
def getDataPunch(request):
    # person = {'name':'Juan dela Cruz', 'age':28}
    punchlog = PunchLog.objects.all()
    punchserializer = PunchSerializer(punchlog, many=True)
    return Response(punchserializer.data)

@api_view(['GET'])
def getDataShift(request):
    shift = ManShift.objects.all()
    shiftserializer = ShiftSerializer(shift, many=True)
    return Response(shiftserializer.data)

@api_view(['POST'])
def addPunchLog(request):
    serializer = PunchSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


