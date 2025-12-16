
from ast import Return
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
import random
import hashlib
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from collections import defaultdict
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from web_app.serializers import *
from core_app.models import *
from core_app.serializers import *
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
from rest_framework.generics import ListAPIView    , RetrieveAPIView
from datetime import date, timedelta
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta ,time
from django.utils.timezone import now
from django.db.models import Min, Max
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework import generics   
from django.db.models import Count
from django.db.models.functions import ExtractMonth
import calendar        
import datetime 
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *



# create department api
class DepartmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Department created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# create designation api
class DesignationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
                print("Decrypted Request:", decrypted_data)
                # Replace request.data with decrypted version
                data = decrypted_data
        else:
                print("Normal  Request:", request.data)
                data = request.data
        serializer = DesignationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Designation created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) 



# list all departments
class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response({
            "success": True,
            "message": "Departments fetched successfully",
            "data": serializer.data
        })

# list all designations
class DesignationListView(APIView): 
    permission_classes =[IsAuthenticated]
    def get(self, request):
        designations = Designation.objects.all()
        serializer = DesignationSerializer(designations, many=True)
        return Response({
            "success": True,
            "message": "Designations fetched successfully",
            "data": serializer.data
        })


# employee notification by employee id
class NotificationLogByUserAPIView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee_id = self.kwargs.get('user_id')  # The URL parameter is still named user_id for backward compatibility
        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
            user = employee.user
            return NotificationLog.objects.filter(user=user).order_by('-timestamp')
        except EmployeeDetail.DoesNotExist:
            return NotificationLog.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })

# notification log edit api
class NotificationLogEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        log = get_object_or_404(NotificationLog, pk=pk)
        serializer = NotificationSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Notification log updated successfully",
                "data": serializer.data
            })
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# employees today birthdays        
      
class TodayBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        employees = EmployeeDetail.objects.filter(
            dob__month=today.month,
            dob__day=today.day
        )

        if not employees.exists():
            return Response(
                {
                    "success": False,
                    "message": "No birthdays today."
                },
                status=status.HTTP_200_OK
            )

        serializer = EmployeebirthdaySerializer(employees, many=True)
        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
#employees tomarow birthday
class TomorrowBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tomorrow = date.today() + timedelta(days=1)
        employees = EmployeeDetail.objects.filter(
            dob__month=tomorrow.month, dob__day=tomorrow.day
        )

        if employees.exists():
            serializer = EmployeebirthdaySerializer(employees, many=True)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": "No birthdays tomorrow"
            }, status=status.HTTP_200_OK)



#employees upcoming birthday comming 7 month
class UpcomingBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        six_months_later = today + timedelta(days=183)  # approx 6 months

        # Extract month/day for filtering
        today_month, today_day = today.month, today.day
        end_month, end_day = six_months_later.month, six_months_later.day

        if today_month <= end_month:
            # Case 1: Both in same year range
            employees = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month, dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )
        else:
            # Case 2: Range spans year-end (e.g. Oct → Mar)
            employees = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month) |
                Q(dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )

        if not employees.exists():
            return Response(
                {"success": False, "message": "No birthdays in the next 6 months."},
                status=status.HTTP_200_OK
            )

        serializer = EmployeebirthdaySerializer(employees, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )

# listing birthday todays , tommorow and upcoming  in single api
class BirthdayListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        six_months_later = today + timedelta(days=183)  # ≈ 6 months

        # --- TODAY ---
        today_birthdays = EmployeeDetail.objects.filter(
            dob__month=today.month,
            dob__day=today.day
        )

        # --- TOMORROW ---
        tomorrow_birthdays = EmployeeDetail.objects.filter(
            dob__month=tomorrow.month,
            dob__day=tomorrow.day
        )

        # --- UPCOMING (next 6 months) ---
        today_month, today_day = today.month, today.day
        end_month, end_day = six_months_later.month, six_months_later.day

        if today_month <= end_month:
            upcoming_birthdays = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month, dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )
        else:
            # Year wrap-around (e.g. Oct → Mar)
            upcoming_birthdays = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month) |
                Q(dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )

        # Serialize all data
        today_data = EmployeebirthdaySerializer(today_birthdays, many=True).data
        tomorrow_data = EmployeebirthdaySerializer(tomorrow_birthdays, many=True).data
        upcoming_data = EmployeebirthdaySerializer(upcoming_birthdays, many=True).data

        # Response format
        return Response({
            "success": True,
            "message": "Birthday data fetched successfully",
            "today_birthdays": today_data if today_data else [],
            "tomorrow_birthdays": tomorrow_data if tomorrow_data else [],
            "upcoming_birthdays": upcoming_data if upcoming_data else [],
         
        }, status=status.HTTP_200_OK)    

# birthday wishes
class TodayBirthdaywishAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_today_birthdays(self):
        today = date.today()
        return EmployeeDetail.objects.filter(
            dob__month=today.month, dob__day=today.day
        )

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data

        """POST API: Send wishes + log them"""
        employees = self.get_today_birthdays()
        if not employees.exists():
            return Response({
                "success": False,
                "message": "No birthdays today to send wishes"
            }, status=status.HTTP_200_OK)

        #  Individual wishes
        for emp in employees:
            wish_message = f"Happy Birthday {emp.first_name}! 🎉"
            title = "Birthday Wish"
            NotificationLog.objects.create(
                user=emp.user,      # save employee's user, not request.user
                action=wish_message,
                title=title
            )

        

        return Response({
            "success": True,
            "message": "Birthday wishes sent & logged successfully"
        }, status=status.HTTP_201_CREATED)


#birthday wish id wise       
class TodayBirthdayWishidAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        POST API: Send wish to a specific employee by ID.
        URL: /api/birthday-wish/<pk>/
        """
        try:
            emp = EmployeeDetail.objects.get(pk=pk)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": f"Employee with id {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        if emp.dob.month != today.month or emp.dob.day != today.day:
            return Response({
                "success": False,
                "message": f"Today is not {emp.first_name}'s birthday"
            }, status=status.HTTP_400_BAD_REQUEST)

        wish_message = (
            f"Happy Birthday {emp.first_name}!  "
           # f"May your day be filled with laughter, love, and wonderful moments!"
        )

        NotificationLog.objects.create(
            user=emp.user,
            action=wish_message,
            title = "Birthday Wish"
        )

        return Response({
            "success": True,
            "message": "Birthday wish sent & logged successfully",
            "wish": {
                "employee_id": emp.pk,
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "wish": wish_message,
                "profile_url": f"/employees/{emp.pk}/"
            }
        }, status=status.HTTP_201_CREATED)
    

# list all notifications of the login user
class AdminNotificationLogListAPIView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(user=self.request.user).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })
    

# branch creation listing api 

class BranchCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Branch created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        branches = Branch.objects.all()
        serializer = BranchSerializer(branches, many=True)
        return Response({
            "success": True,
            "message": "Branches fetched successfully",
            "data": serializer.data
        })    
    


    # privacy policy add list
class  AddListPrivacyPolicyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        # check if a policy already exists
        if PrivacyPolicy.objects.exists():
            existing_policy = PrivacyPolicy.objects.latest('created_at')
            serializer = PrivacyPolicySerializer(existing_policy)
            return Response({
                "success": True,
                "message": "Privacy Policy already exists.Edit the existing one.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        #  Otherwise, create a new one
        serializer = PrivacyPolicySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Privacy Policy created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        policies = PrivacyPolicy.objects.all().order_by('-created_at')
        serializer = PrivacyPolicySerializer(policies, many=True)
        return Response({
            "success": True,
            "message": "Privacy Policies fetched successfully",
            "data": serializer.data
        })  
    

# privacy policy edit api
class PrivacyPolicyEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        policy = get_object_or_404(PrivacyPolicy, pk=pk)
        serializer = PrivacyPolicySerializer(policy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Privacy Policy updated successfully",
                "data": serializer.data
            })
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) 
    

# Terms and conditions sessions        
class AddListTermsAndConditionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        """
        Create a new Terms and Conditions entry if not exists,
        otherwise return the existing one instead of creating duplicates.
        """
        # Check if a Terms and Conditions entry already exists
        existing_terms = TermsAndConditions.objects.first()
        if existing_terms:
            serializer = TermsAndConditionsSerializer(existing_terms)
            return Response({
                "success": True,
                "message": "Terms and Conditions entry already exists. Edit the existing one.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        # If no entry exists, create a new one
        serializer = TermsAndConditionsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Terms and Conditions created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        List all Terms and Conditions entries, ordered by latest created.
        """
        terms = TermsAndConditions.objects.all().order_by('-created_at')
        serializer = TermsAndConditionsSerializer(terms, many=True)
        return Response({
            "success": True,
            "message": "Terms and Conditions fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
class TermsAndConditionsEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data

        terms = get_object_or_404(TermsAndConditions, pk=pk)
        
  
        serializer = TermsAndConditionsSerializer(terms, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Terms and Conditions updated successfully",
                "data": serializer.data
            })
        
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)    


class AddListAboutUsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        """
        Create a new About Us entry if not exists, otherwise return the existing one.
        """
   
        existing_about = AboutUs.objects.first()
        if existing_about:
            serializer = AboutsessionSerializer(existing_about)
            return Response({
                "success": True,
                "message": "About Us entry already exists. Edit the existing one.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

     
        serializer = AboutsessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "About Us created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        List all About Us entries, ordered by latest updated.
        """
        about_us_entries = AboutUs.objects.all().order_by('-updated_at')
        serializer = AboutsessionSerializer(about_us_entries, many=True)
        return Response({
            "success": True,
            "message": "About Us entries fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
class AboutUsEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        # Get the About Us object or return 404
        about = get_object_or_404(AboutUs, pk=pk)
        
        # Partial update serializer
        serializer = AboutsessionSerializer(about, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "About Us updated successfully",
                "data": serializer.data
            })
        
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
     #  search project managers by name 


# branch search api 
class SearchBranchName(APIView):
    permmission_classes = [IsAuthenticated]

    def get(self, request):
        search_name = request.query_params.get("search", "").strip().lower()
        branches = Branch.objects.all()

        matched = []

        for branch in branches:
            decrypted_name = decrypt_value(branch.name).strip()

            #  Case-insensitive search
            if not search_name or search_name in decrypted_name.lower():
                branch.name = decrypted_name  # show decrypted name in response
                matched.append(branch)

        serializer = BranchSerializer(matched, many=True)

        return Response({
            "success": True,
            "message": "Branches listed successfully.",
            "count": len(matched),
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    


# month wise productivity and stats  in productivity dashboard all employees
class MonthlyProductivityCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        current_month = today.month
        current_year = today.year

        attendances = Attendance.objects.filter(date__year=current_year, date__month=current_month)

        total_working_hours = timedelta(0)
        total_break_hours = timedelta(0)
        total_productive_hours = timedelta(0)
        total_overtime_hours = timedelta(0)

        employees = EmployeeDetail.objects.all()

        for emp in employees:
            emp_att = attendances.filter(employee=emp)
            daily_attendance = emp_att.values('date').annotate(first_in=Min('in_time'), last_out=Max('out_time'))

            for day in daily_attendance:
                first_in = day['first_in']
                last_out = day['last_out']

                if not first_in or not last_out:
                    continue

                total_worked = last_out - first_in
                standard_work = timedelta(hours=8,minutes=30)
                break_time = timedelta(hours=1)

                productive_time = total_worked - break_time if total_worked > break_time else timedelta(0)
                overtime = total_worked - standard_work if total_worked > standard_work else timedelta(0)

                total_working_hours += total_worked
                total_break_hours += break_time
                total_productive_hours += productive_time
                total_overtime_hours += overtime

        # Convert to hours
        def td_to_hours(td):
            return round(td.total_seconds() / 3600, 2)

        response_data = {
            "total_working_hours": td_to_hours(total_working_hours),
            "break_hours": td_to_hours(total_break_hours),
            "productive_hours": td_to_hours(total_productive_hours),
            "overtime_hours": td_to_hours(total_overtime_hours)
        }

        return Response({
            "success": True,
            "message": "Monthly productivity count fetched successfully",
            "month": current_month,
            "year": current_year,
            "data": response_data
        })

# working hours all employees cards 
class WorkingHoursallempView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        now = timezone.now()

        # Option: include employee-level details if ?details=1 or ?details=true
        details_flag = str(request.query_params.get("details", "")).lower() in ("1", "true", "yes")

        # Date ranges
        week_start = today - timedelta(days=today.weekday())   # Monday
        month_start = today.replace(day=1)                     # 1st of the month

        # Overtime threshold (8.5 hours)
        OVERTIME_LIMIT_SECONDS = 8.5 * 3600  # 30600 seconds

        # Totals
        daily_total_seconds = 0
        weekly_total_seconds = 0
        monthly_total_seconds = 0
        monthly_overtime_total_seconds = 0

        # Per-employee containers (only used when details_flag True)
        daily_data = {}
        weekly_data = {}
        monthly_data = {}
        overtime_data = {}

        # Fetch attendances for the month (covers weekly & daily ranges)
        attendances = Attendance.objects.filter(date__gte=month_start, date__lte=today)

        for att in attendances:
            if not att.in_time:
                continue

            end_time = att.out_time or now
            worked_seconds = (end_time - att.in_time).total_seconds()

            # Totals
            if att.date == today:
                daily_total_seconds += worked_seconds
            if week_start <= att.date <= today:
                weekly_total_seconds += worked_seconds
            monthly_total_seconds += worked_seconds

            # Overtime (per-day basis)
            if worked_seconds > OVERTIME_LIMIT_SECONDS:
                monthly_overtime_total_seconds += (worked_seconds - OVERTIME_LIMIT_SECONDS)

            # Build per-employee details only if requested
            if details_flag:
                emp_id = att.employee.employee_id
                emp_name = f"{att.employee.first_name} {att.employee.last_name}"

                if emp_id not in daily_data:
                    daily_data[emp_id] = {"name": emp_name, "seconds": 0}
                    weekly_data[emp_id] = {"name": emp_name, "seconds": 0}
                    monthly_data[emp_id] = {"name": emp_name, "seconds": 0}
                    overtime_data[emp_id] = {"name": emp_name, "overtime_seconds": 0}

                if att.date == today:
                    daily_data[emp_id]["seconds"] += worked_seconds
                if week_start <= att.date <= today:
                    weekly_data[emp_id]["seconds"] += worked_seconds
                monthly_data[emp_id]["seconds"] += worked_seconds
                if worked_seconds > OVERTIME_LIMIT_SECONDS:
                    overtime_data[emp_id]["overtime_seconds"] += (worked_seconds - OVERTIME_LIMIT_SECONDS)

        # Helper to convert seconds -> hours
        def sec_to_hours(s): 
            return round(s / 3600, 2)

        # Base response
        response = {
            "success": True,
            "message": "All employees' today, weekly, monthly, and overtime working hours retrieved successfully.",
            "date": str(today),
            "daily": {
                "total_hours_today": sec_to_hours(daily_total_seconds)
            },
            "weekly": {
                "total_hours_weekly": sec_to_hours(weekly_total_seconds)
            },
            "monthly": {
                "total_hours_monthly": sec_to_hours(monthly_total_seconds),
                "total_overtime_hours_monthly": sec_to_hours(monthly_overtime_total_seconds)
            }
        }

        # Attach per-employee details only if ?details=1 or ?details=true
        if details_flag:
            response["daily"]["employee_details"] = [
                {"employee_id": emp_id, "name": info["name"], "worked_hours": round(info["seconds"] / 3600, 2)}
                for emp_id, info in daily_data.items()
            ]
            response["weekly"]["employee_details"] = [
                {"employee_id": emp_id, "name": info["name"], "worked_hours": round(info["seconds"] / 3600, 2)}
                for emp_id, info in weekly_data.items()
            ]
            response["monthly"]["employee_details"] = [
                {"employee_id": emp_id, "name": info["name"], "worked_hours": round(info["seconds"] / 3600, 2)}
                for emp_id, info in monthly_data.items()
            ]
            response["monthly"]["employee_overtime_details"] = [
                {"employee_id": emp_id, "name": info["name"], "overtime_hours": round(info["overtime_seconds"] / 3600, 2)}
                for emp_id, info in overtime_data.items() if info["overtime_seconds"] > 0
            ]

        return Response(response)
    
