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
