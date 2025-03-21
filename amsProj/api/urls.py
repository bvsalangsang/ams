from django.urls import path
from . import views

urlpatterns = [
    path('api/get-data-punch', views.getDataPunch),
    path('api/get-data-shift', views.getDataShift),
    path('api/add-punch', views.addPunchLog)
]