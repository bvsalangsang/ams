from django import forms
from .models import *

class EventForm(forms.ModelForm):
    class Meta:
        model = ManEvent
        fields = ['eventNo','eventName','description']
        widgets = {
            'eventNo':forms.TextInput(attrs={'class':'form-control','style':'margin-bottom:10px'}),
            'eventName':forms.TextInput(attrs={'class':'form-control', 'placeholder':'Event Name' }),
            'description':forms.Textarea(attrs={'rows':'4', 'class':'form-control','placeholder':'Description'}),
        }

class EventTypeForm(forms.ModelForm):
    class Meta:
        model = ManEventType
        fields = ['eventTypeNo', 'eventType', 'isActive']
        widgets = {
            'eventTypeNo': forms.TextInput(attrs={'class': 'form-control', 'style': 'margin-bottom:10px'}),
            'eventType': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Type'}),
            'isActive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = ManSchedule
        fields = ['schedId', 'locationId', 'eventNo', 'startDate', 'endDate', 'startTime', 'endTime', 'isActive']
        widgets = {
            'schedId': forms.TextInput(attrs={'class': 'form-control', 'style': 'margin-bottom:10px'}),
            'locationId': forms.Select(attrs={'class': 'form-control'}),
            'eventNo': forms.Select(attrs={'class': 'form-control'}),
            'startDate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'endDate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'startTime': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'startGrace': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'endTime': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'endGrace': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'isActive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }