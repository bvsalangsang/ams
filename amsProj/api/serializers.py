from rest_framework import serializers
from amsApp.models import *

class PunchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PunchLog
        fields  = '__all__'

class ShiftSerializer(serializers.ModelSerializer):
    class Meta: 
        model = ManShift
        fields  = '__all__'

class SytemInfoSerializer(serializers.ModelSerializer):
    class Meta: 
        model = sysInfo
        fields  = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta: 
        model = ManSchedule
        fields  = '__all__'