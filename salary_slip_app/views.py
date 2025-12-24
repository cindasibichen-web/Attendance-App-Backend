from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .utils import generate_salary_pdf
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
from datetime import date
from core_app.models import *
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .serializers import *
# Create your views here.

# upload salary pdf for the employee
class SalarypdfAPIView(APIView):
    """
    Create a new Salary History record with PDF upload.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SalarypdfSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    
                    
                      "success": True,
                    "message": "Salary history created successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# upload excel sheet for salary slip 
class SalaryExcelUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "Please upload an Excel file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            df = pd.read_excel(file)

            required_cols = [
                'Sl.No', 'Emp. No', 'Name', 'Bank Name', 'Bank A/C No', 'IFSC Code',
                'Department', 'Designation', 'Basic Salary', 'Total Work',
                'LOP Day', 'Paid Day Earnings', 'Total Deductions', 'Net Pay', 'Signature'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return Response(
                    {"error": f"Missing columns: {', '.join(missing_cols)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_records = []
            skipped_records = []

            today = date.today()
            current_month = today.month
            current_year = today.year

            for _, row in df.iterrows():
                employee_id = row['Emp. No']

                try:
                    employee = get_object_or_404(EmployeeDetail, employee_id=employee_id)
                except Exception:
                    skipped_records.append(
                        {"employee_id": employee_id, "reason": "Employee not found"}
                    )
                    continue

                # ✅ Check if salary for this employee and this month already exists
                already_exists = SalaryHistory.objects.filter(
                    employee=employee,
                    effective_date__year=current_year,
                    effective_date__month=current_month
                ).exists()

                if already_exists:
                    skipped_records.append(
                        {"employee_id": employee_id, "reason": "Salary already exists for this month"}
                    )
                    continue

                employee_data = {col: row[col] for col in required_cols}
                pdf_relative_path = generate_salary_pdf(employee_data)

                salary_record = SalaryHistory.objects.create(
                    employee=employee,
                    amount=row['Net Pay'],
                    effective_date=today,
                    pdf_file=pdf_relative_path
                )

                created_records.append(SalarypdfSerializer(salary_record).data)

            return Response({
                "success": True,
                "message": f"{len(created_records)} new salary slips generated, {len(skipped_records)} skipped.",
                "created": created_records,
                "skipped": skipped_records
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
 # list of salary slips for the employee
class SalarySlipListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response(
                {"error": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )   
        salary_slips = SalaryHistory.objects.filter(employee=employee).order_by('-effective_date')
        serializer = SalarypdfSerializer(salary_slips, many=True)   
        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

#  list of salary slips for the logged in user
class LoginUserSalarySlipAPIView(APIView):
    permission_classes  =[IsAuthenticated]
    def get(self, request):
        User = request.user
        try:
            employee = EmployeeDetail.objects.get(user = User)
        except EmployeeDetail.DoesNotExist:
            return Response(
                {"error": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )   
        salary_slips = SalaryHistory.objects.filter(employee=employee).order_by('-effective_date')
        serializer = SalarypdfSerializer(salary_slips, many=True)   
        return Response(
            {
                "success": True,

                "message": "Salary slips fetched successfully",
                
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class SalaryComponentCreateAPIView(APIView):

    def post(self, request):
        serializer = SalaryComponentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Salary component created successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "success": False,
                "message": "Validation error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )  
        
        
        

class SalaryComponentListAPIView(APIView):

    def get(self, request):
        components = SalaryComponent.objects.all().order_by("-id")
        serializer = SalaryComponentSerializer(components, many=True)

        return Response(
            {
                "success": True,
                "message": "Salary components fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        ) 
        
        
        
class SalaryComponentUpdateAPIView(APIView):

    def patch(self, request, pk):
        try:
            component = SalaryComponent.objects.get(pk=pk)
        except SalaryComponent.DoesNotExist:
            return Response(
                {"success": False, "message": "Salary component not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SalaryComponentSerializer(
            component, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Salary component updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )      
    

      
        
class SalaryComponentDeleteView(APIView):

    def delete(self, request, pk):
        component = get_object_or_404(SalaryComponent, pk=pk)
        component.delete()

        return Response(
            {
                "success": True,
                "message": "Salary component deleted successfully"
            },
            status=status.HTTP_200_OK
        )    