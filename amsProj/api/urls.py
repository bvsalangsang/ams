from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/api/get-data-punch', views.getDataPunch),
    path('dashboard/api/get-data-shift', views.getDataShift),
    path('dashboard/api/add-punch', views.addPunchLog),
    path('dashboard/api/add-tamper', views.addTamperLog),
    path('dashboard/api/get-server-time/', views.serverTime),
    path('dashboard/api/get-punch-by-date/', views.getPunchByDate),
    path('dashboard/api/get-punch-by-id/', views.getPunchByPdsId),
    path('dashboard/api/get-sysinfo/', views.getSysInfo),
    path('dashboard/api/get-schedule/', views.getDataSchedule),
    path('dashboard/api/get-schedule-by-date/', views.getScheduleByDate),
    path('dashboard/api/get-location-by-id/', views.getLocationById),
]