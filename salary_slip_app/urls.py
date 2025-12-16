from django.urls import path
from . views import *

urlpatterns = [


    path("salary-component-create/", SalaryComponentCreateAPIView.as_view(), name="salary-component-create"),
    path("salary-component-list/", SalaryComponentListAPIView.as_view(),name="salary-component-list"),
    path("salary-component-update/<int:pk>/", SalaryComponentUpdateAPIView.as_view(),name="salary-component-update"),
    path('salary-pdf-upload/', SalarypdfAPIView.as_view(), name='salary-pdf-upload'),
    path('salary-excel-upload/', SalaryExcelUploadAPIView.as_view(), name='salary-excel-upload'),
    path('login-user-salary-slip/', LoginUserSalarySlipAPIView.as_view(), name='login-user-salary-slip'),
    path('list-salary-slip/<int:employee_id>/', SalarySlipListAPIView.as_view(), name='salary-slip-generate'),

] 