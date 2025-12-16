from ast import Return
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
from datetime import date, timedelta, time ,datetime
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Min, Max
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework import generics   
from django.db.models import Count
from django.db.models.functions import ExtractMonth
import calendar        
import datetime 
from core_app.utils.encrypt_decrypt_data  import *
from core_app.utils.transit_encryption import *




# get count of total pending project approvals and also total pending leave approvals
class DashboardPendingApprovalsCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to view this data."},
                status=status.HTTP_403_FORBIDDEN
            )

        pending_projects_count = Project.objects.filter(status="Pending").count()
        pending_leaves_count = Leave.objects.filter(status="Pending").count()
        employee = EmployeeDetail.objects.filter(user=user).first()

        profile_pic_url = None
        if employee and employee.profile_pic:
            profile_pic_url = request.build_absolute_uri(employee.profile_pic.url)


        user_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "profile_pic": profile_pic_url
        }

        return Response({
            "success": True,
            "message": "Pending approvals count fetched successfully.",
            "data": {
                "user_data": user_data,
                "pending_projects": pending_projects_count,
                "pending_leaves": pending_leaves_count
            }
        }, status=status.HTTP_200_OK)



# total counts employes  attendance in the employee dashboard     
class AttendanceSummaryView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        # Get today's date
        today = now().date()
        last_7_days = today - timedelta(days=7)

        # Attendance summary (today only)
        total_employees = EmployeeDetail.objects.count()
        present_count = Attendance.objects.filter(date=today, status__in=["Present","Late"]).count()
        absent_count = Attendance.objects.filter(date=today, status__iexact="Absent").count()
        onlineemployee_count = EmployeeDetail.objects.filter(job_type__iexact="onlineemployee").count()
        onlineintern_count = EmployeeDetail.objects.filter(job_type__iexact="onlineintern").count()
        offlineemployee_count = EmployeeDetail.objects.filter(job_type__iexact="offlineemployee").count()
        offlineintern_count = EmployeeDetail.objects.filter(job_type__iexact="offlineintern").count()


        # Employee stats
        new_employees_today = EmployeeDetail.objects.filter(created_at__date=today).count()
        # new_employees_last_7_days = EmployeeDetail.objects.filter(created_at__date__gte=last_7_days).count()

        data = {
            "total_employees": total_employees,
            "active": present_count,
            "inactive": absent_count,
            "new_employees_today": new_employees_today,
            "onlineemployee_count": onlineemployee_count,
            "onlineintern_count": onlineintern_count,
            "offlineemployee_count": offlineemployee_count,
            "offlineintern_count": offlineintern_count,
            # "new_employees_last_7_days": new_employees_last_7_days,
        }

        response = {
            "status": True,
            "message": "Attendance summary fetched successfully",
            "data": data,
        }

        return Response(response)



# todays attendance count  all employees
class TodaysAttendanceCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        # Get each employee's first punch-in record for today
        first_punches = (
            Attendance.objects.filter(date=today)
            .values("employee")
            .annotate(first_in=Min("in_time"))
        )

        present_count = 0
        late_count = 0

        for record in first_punches:
            first_in = record["first_in"]
            if first_in:
                # Convert to local time if timezone-aware
                local_in_time = timezone.localtime(first_in)
                punch_time = local_in_time.time()

                # ✅ Compare correctly
                if punch_time <= time(9, 40):
                    present_count += 1
                else:
                    late_count += 1

        # Leave count (unique employees on leave today)
        leave_count = Leave.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status="Approved"
        ).values("employee").distinct().count()

        total_employee_count = EmployeeDetail.objects.filter(user__is_active=True).count()

        return Response({
            "success": True,
            "date": today,
            "total_employee_count":total_employee_count,
            "present_count": present_count,
            "late_count": late_count,
            "leave_count": leave_count
        })



# all employees daily checkin checkout details
class AllTodaysEmployeeCheckinCheckOutDetails(APIView):
    permission_classes = [IsAuthenticated] 
    def get(self, request):
        today = date.today()

        # Aggregate per employee: earliest in, latest out
        qs = (
            Attendance.objects.filter(date=today)
            .values("employee_id", "employee__first_name")
            .annotate(
                first_in=Min("in_time"),
                last_out=Max("out_time")
            )
            .order_by("employee__first_name")
        )

        data = []
        cutoff_time = time(9, 40)  # 09:40 AM cutoff

        for record in qs:
            first_in = record["first_in"]
            last_out = record["last_out"]

            # -------------------
            # Late check
            # -------------------
            is_late = False
            late_duration = "00 h 00 m"

            if first_in:
                # Convert to local timezone
                first_in_local = first_in.astimezone()
                first_in_clock = first_in_local.time()

                # Calculate late duration in seconds
                delta_seconds = (
                    first_in_clock.hour * 3600 + first_in_clock.minute * 60 + first_in_clock.second
                    - cutoff_time.hour * 3600 - cutoff_time.minute * 60
                )

                if delta_seconds > 0:
                    is_late = True
                    hours, remainder = divmod(delta_seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    late_duration = f"{hours:02d} h {minutes:02d} m"
                else:
                    is_late = False
                    late_duration = "00 h 00 m"

            # -------------------
            # Production hours
            # -------------------
            production_hours = "00:00:00"
            if first_in and last_out:
                delta = last_out - first_in
                total_seconds = int(delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                production_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            data.append({
                "employee_id": record["employee_id"],
                "employee_name": record["employee__first_name"],
                "date": str(today),
                "in_time": first_in.astimezone().strftime("%H:%M:%S") if first_in else None,
                "out_time": last_out.astimezone().strftime("%H:%M:%S") if last_out else None,
                "late": is_late,
                "late_duration": late_duration,
                "production_hours": production_hours,
            })

        return Response({
            "success": True,
            "message": "Employee attendance details listed successfully",
            "date": str(today),
            "total_records": len(data),
            "data": data
        })
    

    

# empployee all attendance details by emp id 
class EmployeeAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_object_or_404(EmployeeDetail, id=employee_id)
        serializer = EmployeeAttendanceSerializer(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })
    

# filter employee attendance by status present , absent , late 
class EmployeeAttendanceFilterByStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        status = request.query_params.get("status")
        status = status.strip().title()

        if status not in ["Present", "Absent", "Late"]:
            return Response({
                "status": False,
                "message": "Invalid status. Must be 'Present', 'Absent', or 'Late'."
            }, status=400)

        # Get the employee
        employee = get_object_or_404(EmployeeDetail, id=employee_id)

        # Filter employee's attendance by status
        latest_status = (
            Attendance.objects.filter(employee=employee, date=OuterRef("date"))
            .order_by("-out_time")
            .values("status")[:1]
        )

        qs = (
            Attendance.objects.filter(employee=employee, status=status)
            .values("date")
            .annotate(
                in_time=Min("in_time"),
                out_time=Max("out_time"),
                status=Subquery(latest_status),
            )
            .order_by("-date")
        )

        # Serialize the grouped daily data
        daily_data = DailyAttendanceSerializer(qs, many=True).data

        # Include employee info
        employee_data = {
            "id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "profile_pic": employee.profile_pic.url if employee.profile_pic else None,
            "employee_id": employee.employee_id,
            "attendances": daily_data,
        }

        return Response({
            "status": True,
            "message": f"Attendance with status '{status}' fetched successfully",
            "data": employee_data,
        })

# past 7 days attendance details
class EmployeeAttendanceViewpast7days(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_object_or_404(EmployeeDetail, id=employee_id)
        serializer = EmployeeAttendanceSerializerpast7days(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })

# list employee attendence details by date range
class AttendanceByDateRangeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get("employee_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not employee_id or not start_date or not end_date:
            return Response({
                "status": False,
                "message": "employee_id, start_date, and end_date are required"
            }, status=400)

        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "status": False,
                "message": "Employee not found"
            }, status=404)

        attendances = Attendance.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        ).order_by("-date")

        serializer = AttendanceSerializer(attendances, many=True)
        return Response({
            "status": True,
            "message": f"Attendance records for {employee.first_name} from {start_date} to {end_date}",
            "data": serializer.data
        })



#employee attendence details edit by admin        
class AttendanceEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        attendance = get_object_or_404(Attendance, pk=pk)
        serializer = AttendanceEditSerializer(attendance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Attendance updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=400)
    


      
# leave details of a employee     
class LeaveDetailsDiagramView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """
        Get leave and attendance summary for a specific employee (id),
        filtered for the current year only.
        """
        try:
            employee = EmployeeDetail.objects.get(id=id)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee not found."
            }, status=404)

        # --- Get current year ---
        current_year = timezone.now().year

        # --- Attendance summary (current year only) ---
        attendance_qs = Attendance.objects.filter(
            employee=employee,
            date__year=current_year
        )

        absent_count = attendance_qs.filter(status__iexact="absent").count()

        # Work From Home (case-insensitive variations)
        wfh_count = attendance_qs.filter(
            Q(attendance_type__iexact="wfh") |
            Q(attendance_type__iexact="work from home")
        ).count()

        # On-time and late counts
        on_time_count = 0
        late_count = 0
        for att in attendance_qs:
            if att.in_time:
                in_time_local = timezone.localtime(att.in_time).time()
                if time(9, 0) <= in_time_local <= time(9, 30):
                    on_time_count += 1
                elif time(9, 31) <= in_time_local <= time(9, 45):
                    late_count += 1

        # --- Leave summary (current year only) ---
        leave_qs = Leave.objects.filter(
            employee=employee,
            start_date__year=current_year
        )

        sick_leave_count = leave_qs.filter(leave_type__icontains="sick").count()

        # --- Prepare data ---
        data = {
            "absent_count": absent_count,
            "sick_leave_count": sick_leave_count,
            "wfh_count": wfh_count,
            "on_time_count": on_time_count,
            "late_count": late_count,
        }

        serializer = AttendanceLeaveSummarydiagramSerializer(data=data)
        serializer.is_valid(raise_exception=False)

        return Response({
            "success": True,
            "id": employee.id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
          #  "current_year": current_year,
            "data": serializer.data
        })

# attendance and leaves counts in the productivity stats dashboard
class AttendanceYearlyStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year=None):
        # Use current year if no year provided
        if year is None:
            # year = datetime.date.today().year
            year = date.today().year

        # Filter attendance by year and include "Present" or "Late" (case-insensitive)
        attendances = Attendance.objects.filter(
            date__year=year
        ).filter(
            Q(status__iexact="Present") | Q(status__iexact="Late")
        )

        # Annotate month-wise count
        monthly_data = (
            attendances.annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Format data for chart (Jan–Dec)
        chart_data = []
        for month_num in range(1, 13):
            month_name = calendar.month_abbr[month_num]
            count = next(
                (item["count"] for item in monthly_data if item["month"] == month_num),
                0
            )
            chart_data.append({"month": month_name, "count": count})

        # Total attendance count for the year
        total_attendance = attendances.count()

        response_data = {
            "success": True,
            "year": year,
            "overall_attendance": total_attendance,
            "monthly_attendance": chart_data,
        }
        
        return Response(response_data)

# leave yearly stats for productivity dashboard  
class LeaveYearlyStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year=None):
        # Use current year if no year provided
        if year is None:
            year = date.today().year

        # Filter leaves for the given year with status "Approved" (case-insensitive)
        leaves = Leave.objects.filter(
            start_date__year=year,
            status__iexact="Approved"
        )

        # Annotate month-wise count based on start_date
        monthly_data = (
            leaves.annotate(month=ExtractMonth("start_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Format data for chart (Jan–Dec)
        chart_data = []
        for month_num in range(1, 13):
            month_name = calendar.month_abbr[month_num]
            count = next(
                (item["count"] for item in monthly_data if item["month"] == month_num),
                0
            )
            chart_data.append({"month": month_name, "count": count})

        # Total approved leave count for the year
        total_leaves = leaves.count()

        response_data = {
            "success": True,
            "year": year,
            "total_approved_leaves": total_leaves,
            "monthly_approved_leaves": chart_data,
        }

        return Response(response_data)


#create shifts by admin
class ShiftCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

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
        serializer = ShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Shift created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# list all shifts api
class ShiftListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shifts = ShiftTable.objects.all().order_by('-id')
        serializer = ShiftSerializer(shifts, many=True)
        return Response({
            "success": True,
            "message": "Shifts fetched successfully",
            "data": serializer.data
        })
    
# edit shift api
class ShiftEditView(APIView):
    permission_classes = [IsAuthenticated] 

    def patch(self , request , pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        shift = get_object_or_404(ShiftTable , pk=pk)
        serializer = ShiftSerializer(shift , data=request.data , partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Shift updated successfully",
                "data": serializer.data
            })
        return Response({
            "success": False,
            "errors": serializer.errors
        } , status=400)   
    
# delete shifts
class ShiftDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        shift = get_object_or_404(ShiftTable, pk=pk)
        shift.delete()
        return Response({
            "success": True,
            "message": "Shift deleted successfully"
        })    

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Return distance in meters between two coordinates"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi/2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c



#  admin punch in punch out for admin
class AdminPunchInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

     
        if user.role != "admin":
            return Response({"status": "failed", "message": "Only admins  can punch-in"}, status=403)


        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response({"status": "failed", "message": "Employee profile not found"}, status=404)

        lat = request.data.get("latitude")
        lon = request.data.get("longitude")

        if lat is None or lon is None:
            return Response({"status": "failed", "message": "Latitude & Longitude required"}, status=400)

        try:
            phone_lat = float(lat)
            phone_lon = float(lon)
        except:
            return Response({"status": "failed", "message": "Invalid latitude/longitude"}, status=400)

  
        office = settings.OFFICE_LOCATION  # {"lat": , "lng": , "radius": }
        distance = calculate_distance(phone_lat, phone_lon, office["lat"], office["lng"])

        if distance > office["radius"]:
            return Response({
                "status": "failed",
                "message": "You are outside the office location!",
                "distance_meters": distance
            }, status=403)

        
        ist = pytz.timezone("Asia/Kolkata")
        now_utc = timezone.now()
        now_ist = now_utc.astimezone(ist)
        today_ist = now_ist.date()

   
        approved_leave = Leave.objects.filter(
            employee=employee,
            start_date__lte=today_ist,
            end_date__gte=today_ist,
            status="Approved"
        ).first()

        if approved_leave:
            approved_leave.status = "Not Taken"
            approved_leave.save()

            NotificationLog.objects.create(
                user=user,
                action=f"Leave on {today_ist} marked as 'Not Taken' due to punch-in.",
                title="Leave Updated"
            )

    
        active_punch = Attendance.objects.filter(
            employee=employee,
            date=today_ist,
            punch_in=True,
            out_time__isnull=True
        ).first()

        if active_punch:
            return Response({
                "status": "failed",
                "message": "You already punched-in. Please punch-out first."
            }, status=400)

       
        shift = employee.employee_shift
        if not shift:
            return Response({"status": "failed", "message": "Shift not assigned"}, status=400)

        start = shift.relaxation_start
        start_dt = ist.localize(datetime.combine(today_ist, start))
        present_end_dt = start_dt + timedelta(minutes=15) 
        punch_dt = now_ist

        # NIGHT SHIFT FIX
        if start > shift.relaxation_end:  
            present_end_dt += timedelta(days=1)
            if punch_dt.time() < start:
                punch_dt += timedelta(days=1)

     
        if punch_dt < start_dt:
            status_value = "Early Punch-in"

            NotificationLog.objects.create(
                user=user,
                title="Early Punch-in",
                action=f"Scheduled: {start.strftime('%H:%M:%S')} | Punched: {now_ist.strftime('%H:%M:%S')}"
            )

        elif start_dt <= punch_dt <= present_end_dt:
            status_value = "Present"

        else:
            status_value = "Late Punch-in"

            NotificationLog.objects.create(
                user=user,
                title="Late Punch-in",
                action=f"Scheduled: {start.strftime('%H:%M:%S')} | Punched: {now_ist.strftime('%H:%M:%S')}"
            )

      
        attendance = Attendance.objects.create(
            employee=employee,
            date=today_ist,
            in_time=now_utc,
            attendance_type="office",
            location=f"{phone_lat},{phone_lon}",
            qr_scan=False,                    # No QR here
            qrsession=None,
            status=status_value,
            punch_in=True
        )

        return Response({
            "status": "success",
            "message": "Punch-in successful",
            "attendance_status": status_value,
            "in_time": now_ist.strftime("%H:%M:%S"),
            "shift": shift.shifts_name,
            "session_count": Attendance.objects.filter(employee=employee, date=today_ist).count()
        }, status=200)



class AdminPunchOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

      
        if user.role != "admin":
            return Response({"status": "failed", "message": "Only employees can punch-out"}, status=403)

       
        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response({"status": "failed", "message": "Employee profile not found"}, status=404)

   
        lat = request.data.get("latitude")
        lon = request.data.get("longitude")

        if not lat or not lon:
            return Response({"status": "failed", "message": "Latitude & Longitude required"}, status=400)

        try:
            phone_lat = float(lat)
            phone_lon = float(lon)
        except:
            return Response({"status": "failed", "message": "Invalid latitude/longitude"}, status=400)

        office = settings.OFFICE_LOCATION
        distance = calculate_distance(phone_lat, phone_lon, office["lat"], office["lng"])

        if distance > office["radius"]:
            return Response({
                "status": "failed",
                "message": "You are outside the office location!",
                "distance_meters": distance
            }, status=403)

     
        now_utc = timezone.now()
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = now_utc.astimezone(ist)

     
        attendance = Attendance.objects.filter(
            employee=employee,
            punch_in=True,
            out_time__isnull=True
        ).order_by("-in_time").first()

        if not attendance:
            return Response({"status": "failed", "message": "No active punch-in found"}, status=400)

     
        shift = getattr(employee, "employee_shift", None)
        if not shift:
            return Response({"status": "failed", "message": "Shift not assigned"}, status=400)

        start_time = shift.relaxation_start
        end_time = shift.relaxation_end

        in_time_ist = attendance.in_time.astimezone(ist)
        base_date = in_time_ist.date()

   
        start_dt = ist.localize(datetime.combine(base_date, start_time))
        end_dt = ist.localize(datetime.combine(base_date, end_time))

        # Night shift handling
        if end_time <= start_time:
            end_dt += timedelta(days=1)
            if in_time_ist.time() <= end_time:
                start_dt = ist.localize(datetime.combine(base_date - timedelta(days=1), start_time))
                end_dt = ist.localize(datetime.combine(base_date, end_time))

        six_hours_after_end = end_dt + timedelta(hours=6)

        if now_ist < end_dt:
            punchout_status = "Early Punch-out"
        elif end_dt <= now_ist <= six_hours_after_end:
            punchout_status = "Punch-out"  # Normal
        else:
            punchout_status = "Late Punch-out"

        duration = now_utc - attendance.in_time

        attendance.out_time = now_utc
        attendance.punch_in = False
        attendance.punchout_status = punchout_status
        attendance.location = f"{phone_lat},{phone_lon}"
        attendance.save()

     
        if punchout_status != "Punch-out":
            NotificationLog.objects.create(
                user=user,
                title=punchout_status,
                action=f"{punchout_status}. Shift end: {end_dt.strftime('%H:%M:%S')}, "
                       f"Punched out at {now_ist.strftime('%H:%M:%S')}"
            )

  
        attendance_date_ist = in_time_ist.date()
        start_range = ist.localize(datetime.combine(attendance_date_ist, datetime.min.time())).astimezone(pytz.UTC)
        end_range = ist.localize(datetime.combine(attendance_date_ist, datetime.max.time())).astimezone(pytz.UTC)

        completed_sessions = Attendance.objects.filter(
            employee=employee,
            out_time__isnull=False,
            in_time__gte=start_range,
            in_time__lte=end_range
        ).count()

       
        return Response({
            "status": "success",
            "message": "Punch-out successful",
            "shift": shift.shifts_name,
            "punchout_status": punchout_status,
            "out_time": now_ist.strftime("%H:%M:%S"),
            "session_duration_hours": round(duration.total_seconds() / 3600.0, 2),
            "completed_sessions_today": completed_sessions
        })
