
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
from core_app.face_utils import generate_face_embedding, compare_faces
import tempfile, os
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *
from django.core.files.base import ContentFile




# # leave applying api
# class LeaveApplyingView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         print("Request Headers:", request.headers) 
#         print("Leave Application Request Data:", request.data) 
#         decrypted_data = decrypt_request_payload(request)

#         if decrypted_data:
#             print("Decrypted Leave Request:", decrypted_data)
#             # Replace request.data with decrypted version
#             data = decrypted_data
#         else:
#             print("Normal Leave Request:", request.data)
#             data = request.data
        
        
#         user = request.user
#         serializer = LeaveSerializer(data=data)

#         if serializer.is_valid():
#             attachment_file = None
#             attachment_base64 = data.get("attachment_base64")
#             attachment_name = data.get("attachment_name", "attachment.bin")

#             if attachment_base64:
#                 file_bytes = base64.b64decode(attachment_base64)
#                 attachment_file = ContentFile(file_bytes, name=attachment_name)
#             start_date = serializer.validated_data.get("start_date")
#             end_date = serializer.validated_data.get("end_date")

#             #  Check if exact same leave (same start & end date) already exists
#             exact_match = Leave.objects.filter(
#                 user=user,
#                 start_date=start_date,
#                 end_date=end_date,
#                 status="Pending"
#             ).first()

#             if exact_match:
#                 return Response({
#                     "success": True,
#                     "message": "Leave already exists for the same date range. No duplicate created.",
#                     "notified_admins": 0
#                 }, status=status.HTTP_200_OK)

#             #  Remove previous leaves with the same start_date before saving the new one
#             existing_same_start_leaves = Leave.objects.filter(user=user, start_date=start_date)
#             deleted_count = existing_same_start_leaves.count()
#             existing_same_start_leaves.delete()

#             #  Save the new (latest) leave application
#             leave = serializer.save(
#                 user=user,
#                 employee=getattr(user, "employee_profile", None),
#                  attachments=attachment_file
#             )

#             #  Determine who to notify
#             if getattr(user, "role", None) in ["admin", "superadmin"]:
#                 admins_qs = User.objects.filter(role="superadmin")
#             else:
#                 admins_qs = User.objects.filter(role__in=["admin", "superadmin"])

#             #  Build notification details
#             employee_id = getattr(user.employee_profile, "employee_id", None)
#             title = "Leave Application"
#             action_message = (
#                 f"Leave request from {user.email} ({employee_id})"
#                 if employee_id else f"Leave request from {user.email}"
#             ) + f" for {leave.start_date} to {leave.end_date}"

#             for admin_user in admins_qs:
#                 NotificationLog.objects.create(user=admin_user, action=action_message, title=title)

#             return Response({
#                 "success": True,
#                 "message": (
#                     "Leave applied successfully. "
#                     f"Removed {deleted_count} old leave(s) with the same start date."
#                     if deleted_count else "Leave applied successfully."
#                 ),
#                 "notified_admins": admins_qs.count()
#             }, status=status.HTTP_201_CREATED)

#         return Response({
#             "success": False,
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)

class LeaveApplyingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(" Request Headers:", request.headers)
        print(" Incoming Request Data:", request.data)

        # ------------------------------
        # Detect encrypted payload
        # ------------------------------
        is_encrypted = (
            "encrypted_key" in request.data and
            "cipher" in request.data
        )

        if is_encrypted:
            print(" Encrypted payload detected")

            decrypted_data = decrypt_request_payload(request)
            if not decrypted_data:
                return Response({
                    "success": False,
                    "message": "Failed to decrypt request payload"
                }, status=status.HTTP_400_BAD_REQUEST)

            print("Decrypted Payload:", decrypted_data)
            data = decrypted_data  # replace request.data
        else:
            print(" Plain Request Payload detected")
            data = request.data

        # ------------------------------
        # Serializer & Processing
        # ------------------------------
        user = request.user
        serializer = LeaveSerializer(data=data)

        if serializer.is_valid():
            attachment_file = None
            attachment_base64 = data.get("attachment_base64")
            attachment_name = data.get("attachment_name", "attachment.bin")

            if attachment_base64:
                file_bytes = base64.b64decode(attachment_base64)
                attachment_file = ContentFile(file_bytes, name=attachment_name)

            start_date = serializer.validated_data.get("start_date")
            end_date = serializer.validated_data.get("end_date")

            # Check duplicate leave
            exact_match = Leave.objects.filter(
                user=user, start_date=start_date, end_date=end_date, status="Pending"
            ).first()

            if exact_match:
                return Response({
                    "success": True,
                    "message": "Leave already exists for same date range.",
                    "notified_admins": 0
                }, status=status.HTTP_200_OK)

            # Remove old leave same start_date
            existing_same_start_leaves = Leave.objects.filter(user=user, start_date=start_date)
            deleted_count = existing_same_start_leaves.count()
            existing_same_start_leaves.delete()

            # Save latest leave
            leave = serializer.save(
                user=user,
                employee=getattr(user, "employee_profile", None),
                attachments=attachment_file
            )

            # Notify admins
            if getattr(user, "role", None) in ["admin", "superadmin"]:
                admins_qs = User.objects.filter(role="superadmin")
            else:
                admins_qs = User.objects.filter(role__in=["admin", "superadmin"])

            employee_id = getattr(user.employee_profile, "employee_id", None)
            title = "Leave Application"
            action_message = (
                f"Leave request from {user.email} ({employee_id})"
                if employee_id else f"Leave request from {user.email}"
            ) + f" for {leave.start_date} to {leave.end_date}"

            for admin_user in admins_qs:
                NotificationLog.objects.create(user=admin_user, action=action_message, title=title)

            return Response({
                "success": True,
                "message": (
                    "Leave applied successfully. "
                    f"Removed {deleted_count} old leave(s)." if deleted_count else "Leave applied successfully."
                ),
                "notified_admins": admins_qs.count()
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# employee leave taken , pending request , balance leave , approved leaves , rejected Leaves , upcoming leaves count api based pn start date and end date 
class DashboardLeaveDetailsCountAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # ---------------------------
        # 1️ Get employee record
        # ---------------------------
        try:
            employee = EmployeeDetail.objects.get(user=user)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee record not found for this user"
            }, status=404)

        # ---------------------------
        # 2️ Date filters
        # ---------------------------
        start_filter = request.query_params.get("start_date")
        end_filter = request.query_params.get("end_date")

        # Default: current month
        today = date.today()
        if not start_filter or not end_filter:
            start_filter = today.replace(day=1)
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_filter = next_month - timedelta(days=1)
        else:
            try:
                start_filter = datetime.strptime(start_filter, "%Y-%m-%d").date()
                end_filter = datetime.strptime(end_filter, "%Y-%m-%d").date()
            except ValueError:
                response =  Response(
                    {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."},
                    status=400
                )
                response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
                return response

        # ---------------------------
        # 3️ Helper functions
        # ---------------------------
        company_holidays = set(
            Holiday.objects.filter(type="Company Holiday").values_list("date", flat=True)
        )

        def get_working_days(start_date, end_date):
            """Count working days excluding Sundays and holidays."""
            count = 0
            current = start_date
            while current <= end_date:
                if current.weekday() != 6 and current not in company_holidays:
                    count += 1
                current += timedelta(days=1)
            return count

        # ---------------------------
        # 4️ Yearly total (Approved)
        # ---------------------------
        current_year = today.year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)

        yearly_leaves = Leave.objects.filter(
            employee=employee,
            status="Approved",
            start_date__lte=year_end,
            end_date__gte=year_start
        )

        total_leave_taken_year = 0
        for leave in yearly_leaves:
            total_leave_taken_year += get_working_days(leave.start_date, leave.end_date)

        # ---------------------------
        # 5️ Monthly filtered leaves
        # ---------------------------
        monthly_leaves = Leave.objects.filter(
            employee=employee,
            start_date__lte=end_filter,
            end_date__gte=start_filter
        )

        # Approved & Rejected → days count
        approved_days = sum(
            get_working_days(l.start_date, l.end_date)
            for l in monthly_leaves.filter(status="Approved")
            if l.start_date and l.end_date
        )

        rejected_days = sum(
            get_working_days(l.start_date, l.end_date)
            for l in monthly_leaves.filter(status="Rejected")
            if l.start_date and l.end_date
        )

        # Pending → count requests
        pending_count = monthly_leaves.filter(status="Pending").count()

        # ---------------------------
        # 6️ Response
        # ---------------------------
        response =  Response({
            "success": True,
            "message": "Leave details count fetched successfully",

            "user_id": user.id,
            "employee_id": employee.id,

            #  Yearly summary
            "total_leave_taken": total_leave_taken_year,

            #  Monthly summary (based on filters)
            "approved_request": approved_days,
            "rejected_request": rejected_days,
            "pending_request": pending_count,

            # "filter_range": {
            #     "start_date": start_filter,
            #     "end_date": end_filter
            # }
        }, status=200)
        response.encrypt_payload = True       
        return response
    # def get(self, request, *args, **kwargs):
    #     user = request.user

    #     # --- Optional date filters ---
    #     start_filter = request.query_params.get("start_date")
    #     end_filter = request.query_params.get("end_date")

    #     leaves = Leave.objects.filter(user=user)

    #     if start_filter and end_filter:
    #         try:
    #             start_filter = datetime.strptime(start_filter, "%Y-%m-%d").date()
    #             end_filter = datetime.strptime(end_filter, "%Y-%m-%d").date()
    #             leaves = leaves.filter(
    #                 start_date__gte=start_filter,
    #                 end_date__lte=end_filter
    #             )
    #         except ValueError:
    #             return Response(
    #                 {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."},
    #                 status=400
    #             )

    #     # ---------------------------
    #     # Exclude Sundays & Company Holidays
    #     # ---------------------------
    #     company_holidays = set(
    #         Holiday.objects.filter(type="Company Holiday").values_list("date", flat=True)
    #     )

    #     def get_working_days(start_date, end_date):
    #         """Return number of working days (excluding Sundays & Company Holidays)."""
    #         count = 0
    #         current = start_date
    #         while current <= end_date:
    #             if current.weekday() != 6 and current not in company_holidays:
    #                 count += 1
    #             current += timedelta(days=1)
    #         return count

    #     # --- Helper: total leave days by status ---
    #     def get_total_days_by_status(status_value):
    #         total_days = 0
    #         for leave in leaves.filter(status=status_value):
    #             if leave.start_date and leave.end_date:
    #                 total_days += get_working_days(leave.start_date, leave.end_date)
    #         return total_days

    #     # --- Count leave days by status ---
    #     approved_days = get_total_days_by_status("Approved")
    #     pending_days = get_total_days_by_status("Pending")
    #     rejected_days = get_total_days_by_status("Rejected")

    #     # --- Upcoming leaves (future approved) ---
    #     today = date.today()
    #     upcoming_days = 0
    #     for leave in leaves.filter(status="Approved", start_date__gt=today):
    #         if leave.start_date and leave.end_date:
    #             upcoming_days += get_working_days(leave.start_date, leave.end_date)

    #     # --- Total leave taken: by year ---
    #     # Assumption: if start/end filters are provided, compute total within that range;
    #     # otherwise use the current calendar year.
    #     today = date.today()
    #     if start_filter and end_filter:
    #         year_start = start_filter
    #         year_end = end_filter
    #     else:
    #         year_start = date(today.year, 1, 1)
    #         year_end = date(today.year, 12, 31)

    #     def get_overlap_days(leave_start, leave_end, range_start, range_end):
    #         # return number of working days (excl Sundays & holidays) for overlap between two ranges
    #         if not leave_start or not leave_end:
    #             return 0
    #         overlap_start = max(leave_start, range_start)
    #         overlap_end = min(leave_end, range_end)
    #         if overlap_start > overlap_end:
    #             return 0
    #         return get_working_days(overlap_start, overlap_end)

    #     total_leave_taken_year = 0
    #     for leave in leaves.filter(status="Approved"):
    #         total_leave_taken_year += get_overlap_days(leave.start_date, leave.end_date, year_start, year_end)

    #     # --- Month-wise (current month only) breakdown ---
    #     current_month = today.month
    #     current_year = today.year
    #     # compute start and end of current month
    #     import calendar
    #     last_day = calendar.monthrange(current_year, current_month)[1]
    #     month_start = date(current_year, current_month, 1)
    #     month_end = date(current_year, current_month, last_day)

    #     approved_month_days = 0
    #     pending_month_days = 0
    #     rejected_month_days = 0
    #     upcoming_month_days = 0

    #     for leave in leaves:
    #         if not leave.start_date or not leave.end_date:
    #             continue

    #         # count overlap with current month based on status
    #         if leave.status == "Approved":
    #             approved_month_days += get_overlap_days(leave.start_date, leave.end_date, month_start, month_end)
    #             # upcoming within month: approved leaves with start_date in future relative to today but within month
    #             if leave.start_date > today and month_start <= leave.start_date <= month_end:
    #                 upcoming_month_days += get_overlap_days(leave.start_date, leave.end_date, month_start, month_end)
    #         elif leave.status == "Pending":
    #             pending_month_days += get_overlap_days(leave.start_date, leave.end_date, month_start, month_end)
    #         elif leave.status == "Rejected":
    #             rejected_month_days += get_overlap_days(leave.start_date, leave.end_date, month_start, month_end)

    #     return Response({
    #         "success": True,
    #         "message": "Leave details count fetched successfully",
    #         "total_leave_taken": total_leave_taken_year,
    #             "approved_leaves": approved_month_days,
    #             "pending_request": pending_month_days,
    #             "rejected_leaves": rejected_month_days,
    #             "upcoming_leaves": upcoming_month_days,
         
    #     })
  

# login employees leave list current year and next year 
class LeaveListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # current_year = timezone.now().year
        two_years = [timezone.now().year, timezone.now().year + 1]
        # current_year = two_years[0]


 
        leaves = Leave.objects.filter(
            user=user,
            start_date__year__in=two_years
        ).order_by('-start_date')

        # If no leaves
        if not leaves.exists():
            response =  Response({
                "success": False,
                "message": "No leave records found.",
                "data": [],
                "summary": {
                    "total_leave_taken_year": 0,
                    "approved_days": 0,
                    "rejected_days": 0,
                    "pending_requests": 0,
                    "not_taken":0
                }
            }, status=status.HTTP_200_OK)
            response.encrypt_payload = True       
            return response

   
        company_holidays = set(
            Holiday.objects.filter(type="Company Holiday").values_list("date", flat=True)
        )

        def  get_working_days(start_date, end_date):
            """Count only weekdays excluding Sundays and holidays."""
            count = 0
            current = start_date
            while current <= end_date:
                if current.weekday() != 6 and current not in company_holidays:
                    count += 1
                current += timedelta(days=1)
            return count

  
        approved_days = 0
        rejected_days = 0
        pending_requests = 0
        not_taken = 0

        for leave in leaves:
            if leave.status == "Approved":
                approved_days += get_working_days(leave.start_date, leave.end_date)
            elif leave.status == "Rejected":
                rejected_days += get_working_days(leave.start_date, leave.end_date)
            elif leave.status == "Pending":
                pending_requests += 1
            elif leave.status == "Not Taken":
                not_taken += get_working_days(leave.start_date, leave.end_date)    

        total_leave_taken_year = approved_days

     
        serializer = LeaveSerializerview(leaves, many=True)
        response =  Response({
            "success": True,
            "message": "Leave records fetched successfully.",
            "data": serializer.data,
            "summary": {
                "total_leave_taken_year": total_leave_taken_year,
                "approved_days": approved_days,
                "rejected_days": rejected_days,
                "pending_requests": pending_requests,
                "not_taken": not_taken
            }
        }, status=status.HTTP_200_OK)
        response.encrypt_payload = True       
        return response


# cancel the leaves by employee
class LeaveCancelView(APIView):
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
        leave_id = data.get("leave_id")
        if not leave_id:
            response =  Response({
                "success": False,
                "message": "leave_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
            response.encrypt_payload = True       
            return response

        leave = get_object_or_404(Leave, id=leave_id)
        leave.status = "Cancelled"
        leave.save()
        response = Response({
            "success": True,
            "message": "Leave cancelled successfully"
        }, status=status.HTTP_200_OK)
        response.encrypt_payload = True      
        return response





class HolidayListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
       
        year = int(request.query_params.get('year', timezone.now().year))
        month = request.query_params.get('month')  

        # -------------------
        # 1. Fetch Company Holidays (prepare both full-year count and month-filtered data)
        # -------------------
        company_qs_full = Holiday.objects.filter(type='Company Holiday', date__year=year)
        company_count = company_qs_full.count()

        # For display, apply month filter if provided
        company_qs_display = company_qs_full
        if month:
            company_qs_display = company_qs_display.filter(date__month=int(month))

        company_data = HolidaySerializer1(company_qs_display, many=True).data

      
        country_holidays = pyholidays.India(years=year)
        public_count = len(country_holidays)

        public_holiday_list = []
        for date_obj, desc in country_holidays.items():
            if month and date_obj.month != int(month):
                continue
            public_holiday_list.append({
                'id': f'public-{date_obj}', 
                'description': desc,
                'date': date_obj,           
                'type': 'Public Holiday',
                'added_by': None
            })

   
        all_holidays = company_data + public_holiday_list

   
        month_wise = defaultdict(list)
        for h in all_holidays:
            # Parse date if it's string (from serializer)
            if isinstance(h['date'], str):
                dt = datetime.strptime(h['date'], "%Y-%m-%d")
            else:
                dt = h['date']  # already a date object

            month_key = dt.month
            month_wise[month_key].append(h)

    
        month_wise = dict(month_wise)

        total_holidays = company_count + public_count

        response =  Response({
            "success": True,
            "message": "Holiday list fetched successfully",
            "total_holidays": total_holidays,
            "data": month_wise
        }, status=status.HTTP_200_OK)
        response.encrypt_payload = True     
        return response
    
