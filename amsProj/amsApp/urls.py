from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('attendance-log/', attendanceLogs, name='attendanceLogs'),
    path('attJsonList/', attJsonList, name='attJsonList'),
    path('event/', shiftView, name='shiftView'),
    path('shiftJsonList/', shiftJsonList, name='shiftJsonList'),
    path('shiftSaveUpdate/', shiftSaveUpdate, name='shiftSaveUpdate'),
    path('deleteShiftView/', deleteShiftView, name='deleteShiftView'),

    path('event-type/', shiftTypeView, name='shiftTypeView'),
    path('shiftTypeJsonList/', shiftTypeJsonList, name='shiftTypeJsonList'),
    path('shiftTypeSaveUpdate/', shiftTypeSaveUpdate, name='shiftTypeSaveUpdate'),
    path('deleteShiftType/', deleteShiftType, name='deleteShiftType'),
    
] 