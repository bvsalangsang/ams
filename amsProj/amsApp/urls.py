from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/attendance-log/', attendanceLogs, name='attendanceLogs'),
    path('dashboard/attJsonList/', attJsonList, name='attJsonList'),
    
    #shift
    # path('dashboard/event/', shiftView, name='shiftView'),
    path('dashboard/shiftJsonList/', shiftJsonList, name='shiftJsonList'),
    path('dashboard/shiftSaveUpdate/', shiftSaveUpdate, name='shiftSaveUpdate'),
    path('dashboard/deleteShiftView/', deleteShiftView, name='deleteShiftView'),

    #event
    path('dashboard/event/', eventView, name='shiftView'),
    path('dashboard/eventJsonList/', eventJsonList, name='eventJsonList'),
    path('dashboard/eventSaveUpdate/', eventSaveUpdateParams, name='eventSaveUpdateParams'),
    path('dashboard/deleteEvent/', deleteEvent, name='deleteEvent'),

    #event type
    path('dashboard/event-type/', eventTypeView, name='eventTypeView'),
    path('dashboard/eventTypeJsonList/', eventTypeJsonList, name='eventTypeJsonList'),
    path('dashboard/eventTypeSaveUpdate/', eventTypeSaveUpdate, name='eventTypeSaveUpdate'),
    path('dashboard/deleteEventType/', deleteEventType, name='deleteEventType'),

    #schedule
    path('dashboard/schedule/', scheduleView, name='scheduleView'),
    path('dashboard/scheduleJsonList/', scheduleJsonList, name='scheduleJsonList'),
    path('dashboard/scheduleSaveUpdate/', scheduleSaveUpdate, name='scheduleSaveUpdate'),

    path('dashboard/event-type/', shiftTypeView, name='shiftTypeView'),
    path('dashboard/shiftTypeJsonList/', shiftTypeJsonList, name='shiftTypeJsonList'),
    path('dashboard/shiftTypeSaveUpdate/', shiftTypeSaveUpdate, name='shiftTypeSaveUpdate'),
    path('dashboard/deleteShiftType/', deleteShiftType, name='deleteShiftType'),
    
    #location
    path('dashboard/map-location/', locationView, name='locationView'),

    #Control Panel
    path('dashboard/set-schedule/', setScheduleView, name='setScheduleView'),
    path('dashboard/setSchedule/', setSchedule, name='setSchedule'),      


] 