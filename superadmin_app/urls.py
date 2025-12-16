from django.urls import path
from . views import *

urlpatterns = [
    path('superadmin_employee_designation_count/', SuperadminEmployeeDesignationCountView.as_view(), name='superadmin_employee_designation_count'),
    
]