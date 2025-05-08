from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
     path('dashboard/attendance-log/', attendanceLogs, name='attendanceLogs'),
    path('dashboard/attJsonList/', attJsonList, name='attJsonList'),
    path('dashboard/event/', shiftView, name='shiftView'),
    path('dashboard/shiftJsonList/', shiftJsonList, name='shiftJsonList'),
    path('dashboard/shiftSaveUpdate/', shiftSaveUpdate, name='shiftSaveUpdate'),
    path('dashboard/deleteShiftView/', deleteShiftView, name='deleteShiftView'),

    path('dashboard/event-type/', shiftTypeView, name='shiftTypeView'),
    path('dashboard/shiftTypeJsonList/', shiftTypeJsonList, name='shiftTypeJsonList'),
    path('dashboard/shiftTypeSaveUpdate/', shiftTypeSaveUpdate, name='shiftTypeSaveUpdate'),
    path('dashboard/deleteShiftType/', deleteShiftType, name='deleteShiftType'),
    
] 