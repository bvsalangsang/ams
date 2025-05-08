from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/api/get-data-punch', views.getDataPunch),
    path('dashboard/api/get-data-shift', views.getDataShift),
    path('dashboard/api/add-punch', views.addPunchLog),
]