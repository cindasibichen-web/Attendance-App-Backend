from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated, AllowAny
from core_app.models import User, EmployeeDetail, EmailOTP, NotificationLog
from core_app.serializers import UserLoginSerializer, EmployeeSerializer
import random
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.generics import ListAPIView
from django.core.mail import send_mail
from core_app.models import User, EmailOTP
import random
import hashlib
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import time
from rest_framework.permissions import BasePermission
from core_app.serializers import *
import qrcode
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from django.db.models import Min, Max
from web_app.serializers import *
import io
import numpy as np
import base64
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
import json
from django.http import JsonResponse
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
import holidays as pyholidays
from datetime import date, datetime
from rest_framework.renderers import JSONRenderer
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *

# get login employee attendence details
class EmployeeAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        employee = user.employee_profile

        attendances_qs = Attendance.objects.filter(employee=employee)

        # Group by date -> get first in_time & last out_time
        daily_summary = (
            attendances_qs
            .values("date")
            .annotate(
                first_in=Min("in_time"),
                last_out=Max("out_time"),
            )
            .order_by("-date")
        )

        # Prepare final structured result
        grouped_data = defaultdict(lambda: defaultdict(list))

        for record in daily_summary:
            year = record["date"].year
            month = record["date"].month

            # fetch attendance instance for serializer
            first_in_att = attendances_qs.filter(
                date=record["date"], in_time=record["first_in"]
            ).first()

            last_out_att = attendances_qs.filter(
                date=record["date"], out_time=record["last_out"]
            ).first()

            if first_in_att:
                first_in_att.in_time = record["first_in"] 
                if last_out_att:
                    first_in_att.out_time = record["last_out"]

                serializer = AttendanceSerializer(first_in_att).data
                grouped_data[year][month].append(serializer)

        # Convert defaultdict → normal dict for JSON response
        grouped_data = {
            str(year): {
                str(month): days
                for month, days in months.items()
            }
            for year, months in grouped_data.items()
        }

        response =  Response({"success": True, "data": grouped_data})

        response.encrypt_payload = True    
        return response   

# get daily punch session summary
class DailyPunchSessionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_profile
        
        # Get date from query params, default to today
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}, status=400)
        else:
            target_date = timezone.now().date()
        
        # Get all attendance records for the target date
        attendances = Attendance.objects.filter(
            employee=employee, 
            date=target_date
        ).order_by('in_time')
        
        # Calculate summary data
        total_sessions = attendances.count()
        completed_sessions = attendances.filter(out_time__isnull=False).count()
        active_session = attendances.filter(out_time__isnull=True, punch_in=True).first()
        
        # Calculate total working hours
        total_working_hours = 0
        session_details = []
        
        for attendance in attendances:
            if attendance.out_time:
                duration = attendance.out_time - attendance.in_time
                hours = duration.total_seconds() / 3600
                total_working_hours += hours
                
                session_details.append({
                    "session_id": attendance.id,
                    "punch_in": attendance.in_time.astimezone().strftime("%H:%M:%S"),
                    "punch_out": attendance.out_time.astimezone().strftime("%H:%M:%S"),
                    "duration_hours": round(hours, 2),
                    "location": attendance.location,
                    "qr_scan": attendance.qr_scan
                })
            else:
                # Active session (punch-in without punch-out)
                session_details.append({
                    "session_id": attendance.id,
                    "punch_in": attendance.in_time.astimezone().strftime("%H:%M:%S"),
                    "punch_out": None,
                    "duration_hours": None,
                    "location": attendance.location,
                    "qr_scan": attendance.qr_scan,
                    "status": "Active"
                })
        
        response =  Response({
            "success": True,
            "date": target_date.strftime("%Y-%m-%d"),
            "summary": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "active_sessions": 1 if active_session else 0,
                "total_working_hours": round(total_working_hours, 2),
                "has_active_punch_in": bool(active_session)
            },
            "sessions": session_details
        })
        response.encrypt_payload = True      
        return response


# login employees presence , absence , leaves count (with late count)
class EmployeePresenceAbsenceLeaveCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_profile

        # Initialize defaultdict
        data = defaultdict(lambda: defaultdict(lambda: {
            "presence_count": 0,
            "late_count": 0,
            "absence_count": 0,
            "leave_count": 0
        }))

        # Current local date
        today = timezone.localtime(timezone.now()).date()

        # -----------------------------
        # 1. Attendance-based presence, absence, late
        # -----------------------------
        attendances = Attendance.objects.filter(employee=employee)

        # Group attendances by date and use only the first punch-in (earliest in_time)
        attendance_by_date = defaultdict(list)
        for att in attendances:
            attendance_by_date[att.date].append(att)

        for att_date, att_list in attendance_by_date.items():
            year, month = att_date.year, att_date.month

            # If any record explicitly marked Absent for the date, count as absent
            if any(a.status == "Absent" for a in att_list):
                data[year][month]["absence_count"] += 1
                continue

            # Find earliest in_time for the date
            in_times = [a.in_time for a in att_list if a.in_time]
            if in_times:
                first_in = min(in_times)
                local_first_in = timezone.localtime(first_in).time()
                if local_first_in <= time(9, 40):
                    data[year][month]["presence_count"] += 1
                else:
                    # Late arrival counts as late + absence
                    data[year][month]["late_count"] += 1
                    data[year][month]["absence_count"] += 1
            else:
                # No in_time recorded that day → absent
                data[year][month]["absence_count"] += 1

        # -----------------------------
        # 2. Company holidays to exclude
        # -----------------------------
        company_holidays = set(
            Holiday.objects.filter(type="Company Holiday").values_list("date", flat=True)
        )

        # -----------------------------
        # 3. Leave-based count (excluding Sundays & holidays)
        # -----------------------------
        leaves = Leave.objects.filter(user=user, status="Approved").values("start_date", "end_date")

        for leave in leaves:
            start = leave["start_date"]
            end = leave["end_date"]

            if not start or not end:
                continue

            current = start
            while current <= end:
                # Exclude Sundays (weekday() == 6) and Company Holidays
                if current.weekday() != 6 and current not in company_holidays:
                    year, month = current.year, current.month
                    data[year][month]["leave_count"] += 1
                current += timedelta(days=1)

        # -----------------------------
        # 4. Sort & format final data
        # -----------------------------
        now = timezone.localtime(timezone.now())
        current_year = now.year
        current_month = now.month

        final_data = {}
        for year in sorted(data.keys(), reverse=True):
            months = data[year]
            sorted_months = sorted(
                months.items(),
                key=lambda x: (x[0] != current_month, -x[0])
            )
            final_data[str(year)] = {str(month): counts for month, counts in sorted_months}

        response =  Response({
            "success": True,
            "message": "Monthly counts listed successfully",
            "data": final_data
        })
        response.encrypt_payload = True     
        return response
    

#login employees daily check in check out details 

class EmployeeAllAttendanceDetailsView(APIView):
    """
    API to get logged-in employee's attendance details for all days.
    Returns attendance grouped by date, with session details and daily summary.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee profile not found"
            }, status=404)

        # Optionally, support date range filtering
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        attendance_qs = Attendance.objects.filter(employee=employee)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                attendance_qs = attendance_qs.filter(date__gte=start_date)
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid start_date format. Use YYYY-MM-DD"
                }, status=400)
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                attendance_qs = attendance_qs.filter(date__lte=end_date)
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid end_date format. Use YYYY-MM-DD"
                }, status=400)

        attendance_qs = attendance_qs.order_by('date', 'in_time')

        if not attendance_qs.exists():
            response =  Response({
                "success": True,
                "message": "No attendance records found.",
                "employee": {
                    "id": employee.id,
                    "employee_id": employee.employee_id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "department": employee.department,
                    "designation": employee.designation,
                    "email": user.email
                },
                "attendance_by_date": [],
                "overall_summary": {
                    "total_days": 0,
                    "total_sessions": 0,
                    "total_working_hours": 0
                }
            }, status=200)
            response.encrypt_payload = True     
            return response

        # Group attendance by date
        from collections import defaultdict
        attendance_by_date = defaultdict(list)
        for att in attendance_qs:
            attendance_by_date[att.date].append(att)

        attendance_details_list = []
        overall_total_sessions = 0
        overall_total_working_hours = 0

        for date, attendances in sorted(attendance_by_date.items()):
            day_sessions = []
            day_total_working_hours = 0
            first_in_time = None
            last_out_time = None
            has_active_session = False

            for attendance in attendances:
                session_duration = None
                if attendance.out_time and attendance.in_time:
                    duration = attendance.out_time - attendance.in_time
                    session_duration = duration.total_seconds() / 3600
                    day_total_working_hours += session_duration
                    if first_in_time is None:
                        first_in_time = attendance.in_time
                    last_out_time = attendance.out_time
                else:
                    has_active_session = True
                    if first_in_time is None:
                        first_in_time = attendance.in_time

                day_sessions.append({
                    "session_id": attendance.id,
                    "in_time": attendance.in_time.astimezone().strftime("%H:%M:%S") if attendance.in_time else None,
                    "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S") if attendance.out_time else None,
                    "attendance_type": attendance.attendance_type,
                    "location": attendance.location,
                    "qr_scan": attendance.qr_scan,
                    "status": attendance.status,
                    "punch_in": attendance.punch_in,
                    "session_duration_hours": round(session_duration, 2) if session_duration else None,
                    "is_active_session": attendance.out_time is None and attendance.punch_in,
                    "created_at": attendance.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": attendance.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                })

            attendance_details_list.append({
                "date": date.strftime("%Y-%m-%d"),
                "sessions": day_sessions,
                "summary": {
                    "total_sessions": len(day_sessions),
                    "first_in_time": first_in_time.astimezone().strftime("%H:%M:%S") if first_in_time else None,
                    "last_out_time": last_out_time.astimezone().strftime("%H:%M:%S") if last_out_time else None,
                    "total_working_hours": round(day_total_working_hours, 2),
                    "has_active_session": has_active_session,
                    "completed_sessions": sum(1 for a in attendances if a.out_time is not None),
                    "active_sessions": sum(1 for a in attendances if a.out_time is None and a.punch_in)
                }
            })

            overall_total_sessions += len(day_sessions)
            overall_total_working_hours += day_total_working_hours

        response =Response({
            "success": True,
            "message": "Attendance details retrieved successfully for all days.",
            "employee": {
                "id": employee.id,
                "employee_id": employee.employee_id,
                "name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "designation": employee.designation,
                "email": user.email
            },
            "attendance_by_date": attendance_details_list,
            "overall_summary": {
                "total_days": len(attendance_details_list),
                "total_sessions": overall_total_sessions,
                "total_working_hours": round(overall_total_working_hours, 2)
            }
        }, status=200)
        response.encrypt_payload = True       
        return response
    

 # get details of first punch in and last punch out details by year , month and day wise of the login employee
# class AttendanceReportView(APIView):
#     """
#     API to get logged-in employee's first punch-in and last punch-out details
#     grouped by year, month, and day.
#     """
#     permission_classes = [IsAuthenticated]

   

#     def get(self, request):
#         user = request.user

#         try:
#             employee = user.employee_profile
#         except EmployeeDetail.DoesNotExist:
#             return Response({
#                 "success": False,
#                 "message": "Employee profile not found"
#             }, status=404)

#         # Fetch all attendances and leaves for the employee
#         attendance_qs = Attendance.objects.filter(employee=employee)
#         leave_qs = Leave.objects.filter(employee=employee)

#         if not attendance_qs.exists() and not leave_qs.exists():
#             return Response({
#                 "success": True,
#                 "message": "No attendance or leave records found.",
#                 "data": {}
#             }, status=200)

#         # Group attendances by date
#         grouped_data = defaultdict(list)
#         for att in attendance_qs:
#             grouped_data[att.date].append(att)

#         final_data = defaultdict(lambda: defaultdict(list))

#         # Get all unique dates from attendance or leave
#         all_dates = set(list(grouped_data.keys()) + list(leave_qs.values_list('requested_date', flat=True)))

#         for date in sorted(all_dates):
#             day_attendances = grouped_data.get(date, [])

#             # First punch-in and last punch-out
#             first_in = min([att.in_time for att in day_attendances if att.in_time], default=None)
#             last_out = max([att.out_time for att in day_attendances if att.out_time], default=None)

#             # Default status
#             status = "absent"
#             attendance_type = None
#             location = None

#             if day_attendances:
#                 # Determine first attendance record (by in_time) to check punctuality
#                 first_att = min(day_attendances, key=lambda x: x.in_time if x.in_time else timezone.datetime.max)
#                 attendance_type = first_att.attendance_type
#                 location = first_att.location

#                 # If first punch-in exists, convert to local time and compare against threshold
#                 if first_att.in_time:
#                     # Convert to local timezone
#                     local_first_in = timezone.localtime(first_att.in_time)
#                     threshold = time(9, 40)
#                     if local_first_in.time() <= threshold:
#                         status = "present"
#                     else:
#                         status = "late"
#                 else:
#                     # No in_time in records → mark absent
#                     status = "absent"

#             # Check leave for this date
#             leave = leave_qs.filter(
#                 start_date__lte=date,
#                 end_date__gte=date
#             ).first()

#             if leave:
#                 leave_status = leave.status.lower()
#                 if leave_status == "approved":
#                     status = "leave"
#                 elif leave_status == "rejected":
#                     status = "absent"
#                 elif leave_status == "not taken":
#                     # Treat as working day — check punch-in time
#                     if first_in:
#                         local_first_in = timezone.localtime(first_in)
#                         threshold = time(9, 40)
#                         if local_first_in.time() <= threshold:
#                             status = "present"
#                         else:
#                             status = "late"
#                     else:
#                         status = "absent"  # If no attendance record at all

#             year = date.year
#             month = date.month

#             daily_summary = {
#                 "date": date.strftime("%Y-%m-%d"),
#                 "first_punch_in": first_in.astimezone().strftime("%H:%M:%S") if first_in else None,
#                 "last_punch_out": last_out.astimezone().strftime("%H:%M:%S") if last_out else None,
#                 "status": status,
#                 "attendance_type": attendance_type,
#                 "location": location
#             }

#             final_data[str(year)][str(month)].append(daily_summary)

#         return Response({
#             "success": True,
#             "message": "First punch-in and last punch-out details with status retrieved successfully.",
#             "data": final_data
#         }, status=200)
from django.utils import timezone
from datetime import datetime, time, timedelta

class AttendanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        
        user = request.user

        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee profile not found"
            }, status=404)

        attendance_qs = Attendance.objects.filter(employee=employee)
        leave_qs = Leave.objects.filter(employee=employee)

        if not attendance_qs.exists() and not leave_qs.exists():
            response =  Response({
                "success": True,
                "message": "No attendance or leave records found.",
                "data": {}
            }, status=200)
            response.encrypt_payload = True       
            return response

        from collections import defaultdict
        grouped_data = defaultdict(list)
        for att in attendance_qs:
            grouped_data[att.date].append(att)

        final_data = defaultdict(lambda: defaultdict(list))
        all_dates = set(list(grouped_data.keys()) + list(leave_qs.values_list('requested_date', flat=True)))

        # ✅ Create timezone-aware max datetime
        aware_max_datetime = timezone.make_aware(datetime.max, timezone.get_current_timezone())

        for date in sorted(all_dates):
            day_attendances = grouped_data.get(date, [])
            first_in = min([att.in_time for att in day_attendances if att.in_time], default=None)
            last_out = max([att.out_time for att in day_attendances if att.out_time], default=None)

            status = "absent"
            attendance_type = None
            location = None

            if day_attendances:
                # ✅ Use timezone-aware max datetime
                first_att = min(
                    day_attendances,
                    key=lambda x: x.in_time if x.in_time else aware_max_datetime
                )
                attendance_type = first_att.attendance_type
                location = first_att.location

                if first_att.in_time:
                    local_first_in = timezone.localtime(first_att.in_time)
                    threshold = time(9, 40)
                    status = "present" if local_first_in.time() <= threshold else "late"
                else:
                    status = "absent"

            leave = leave_qs.filter(start_date__lte=date, end_date__gte=date).first()
            if leave:
                leave_status = leave.status.lower()
                if leave_status == "approved":
                    status = "leave"
                elif leave_status == "rejected":
                    status = "absent"
                elif leave_status == "not taken":
                    if first_in:
                        local_first_in = timezone.localtime(first_in)
                        threshold = time(9, 40)
                        status = "present" if local_first_in.time() <= threshold else "late"
                    else:
                        status = "absent"

            year, month = date.year, date.month
            daily_summary = {
                "date": date.strftime("%Y-%m-%d"),
                "first_punch_in": first_in.astimezone().strftime("%H:%M:%S") if first_in else None,
                "last_punch_out": last_out.astimezone().strftime("%H:%M:%S") if last_out else None,
                "status": status,
                "attendance_type": attendance_type,
                "location": location
            }

            final_data[str(year)][str(month)].append(daily_summary)

        response = Response({
            "success": True,
            "message": "First punch-in and last punch-out details with status retrieved successfully.",
            "data": final_data
        }, status=200)
        response.encrypt_payload = True       
        return response
    



