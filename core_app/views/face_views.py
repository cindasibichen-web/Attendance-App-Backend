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
from django.http import HttpResponse
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *

                                                                                                                    

class FaceVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        print("Leave Application Request Data:", request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Leave Request:", decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data



        user_id = data.get("user_id")
        image_file = request.FILES.get("image")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not user_id or not image_file:
            return Response(
                {"success": False, "error": "user_id and image are required"},
                status=400
            )

        employee = get_object_or_404(EmployeeDetail, user__id=user_id)
        user = employee.user

        # Ensure employee has profile picture
        if not employee.profile_pic:
            return Response({"success": False, "error": "No profile picture found"}, status=404)

        # Ensure employee has face embedding saved
        if not employee.face_encoding:
            profile_embedding = generate_face_embedding(employee.profile_pic.path)
            if not profile_embedding:
                return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
            employee.face_encoding = profile_embedding
            employee.save()

        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in image_file.chunks():
                tmp_file.write(chunk)
            uploaded_path = tmp_file.name

        uploaded_embedding = generate_face_embedding(uploaded_path)
        os.remove(uploaded_path)

        if not uploaded_embedding:
            return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)

        # Compare faces using cosine similarity
        match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.8)

        if not match:
            return Response({
                "success": False,
                "error": "Face does not match. Verification failed.",
                "confidence": confidence
            }, status=401)

        # ✅ Mark Attendance
        today = timezone.localdate()

        # Check approved leave
        approved_leave = Leave.objects.filter(
            employee=employee,
            start_date__lte=today,
            end_date__gte=today,
            status="Approved"
        ).first()

        if approved_leave:
            approved_leave.status = "Not Taken"
            approved_leave.save()

            NotificationLog.objects.create(
                user=user,
                action=f"Leave on {today} marked as 'Not Taken' due to punch-in.",
                title="Leave Updated"
            )

        # Check if already punched in
        active_punch_in = Attendance.objects.filter(
            employee=employee,
            date=today,
            out_time__isnull=True,
            punch_in=True
        ).first()

        if active_punch_in:
            return Response({
                "success": False,
                "message": "You already have an active punch-in. Please punch-out first."
            }, status=400)

        today_punch_count = Attendance.objects.filter(employee=employee, date=today).count()

        # Determine punch-in status (Late / Present)
        ist = pytz.timezone("Asia/Kolkata")
        in_time_utc = timezone.now()
        in_time_ist = in_time_utc.astimezone(ist)

        # late_threshold = time(9, 40)
        # if today_punch_count == 0 and in_time_ist.time() > late_threshold:
        #     status_value = "Late"
        #     NotificationLog.objects.create(
        #         user=user,
        #         action=f"Late punch-in recorded at {in_time_ist.strftime('%H:%M:%S')}",
        #         title=status_value,
        #     )
        # else:
        #     status_value = "Present"
# Get Employee Shift Start Time
        shift = employee.employee_shift
        if not shift:
            shift_start = time(9, 40)  # default 9:40
        else:
            shift_start = shift.relaxation_start

        # Normalize seconds
        punch_time = in_time_ist.time().replace(second=0, microsecond=0)
        shift_start = shift_start.replace(second=0, microsecond=0)

        # Determine status
        if today_punch_count == 0:  # first punch only
            if punch_time > shift_start:
                status_value = "Late"
                NotificationLog.objects.create(
                    user=user,
                    action=f"Late punch-in. Shift start: {shift_start}, punched at {in_time_ist.strftime('%H:%M:%S')}",
                    title="Late"
                )
            else:
                status_value = "Present"
        else:
            status_value = "Present"

        # Save Attendance Record
        Attendance.objects.create(
            employee=employee,
            date=today,
            in_time=in_time_utc,
            attendance_type="WFH",
            status=status_value,
            location=f"{latitude},{longitude}",
            in_selfie=image_file,
            verified_by=user,
            punch_in=True
        )

        return Response({
            "success": True,
            "message": "Face matched and check-in recorded successfully.",
            "confidence": confidence,
            "employee": EmployeeSerializer(employee).data,
            "attendance_type": "WFH",
            "on_site": False,
            "user": UserLoginSerializer(user).data,
        }, status=200)

    # def post(self, request):
    #     user_id = request.data.get("user_id")
    #     image_file = request.FILES.get("image")
    #     latitude = request.data.get("latitude")
    #     longitude = request.data.get("longitude")

    #     if not user_id or not image_file:
    #         return Response({"success": False, "error": "user_id and image are required"}, status=400)

    #     employee = get_object_or_404(EmployeeDetail, user__id=user_id)

    #     if not employee.profile_pic:
    #         return Response({"success": False, "error": "No profile picture found"}, status=404)

    #     # Ensure employee has face embedding
    #     if employee.face_encoding is None:
    #         profile_embedding = generate_face_embedding(employee.profile_pic.path)
    #         if profile_embedding is None:
    #             return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
    #         employee.face_encoding = profile_embedding.tolist()
    #         employee.save()

    #     # Save uploaded file temporarily to generate embedding
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
    #         for chunk in image_file.chunks():
    #             tmp_file.write(chunk)
    #         uploaded_path = tmp_file.name

    #     uploaded_embedding = generate_face_embedding(uploaded_path)
    #     os.remove(uploaded_path)

    #     if uploaded_embedding is None:
    #         return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)

    #     # Compare embeddings
    #     match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.5)

    #     if not match:
    #         return Response({
    #             "success": False,
    #             "error": "Face does not match",
    #             "confidence": confidence
    #         }, status=401)
    #     # ✅ Check for active punch-in
    #     today = timezone.now().date()

    #     approved_leave = Leave.objects.filter(
    #     employee=employee,
    #     start_date__lte=today,
    #     end_date__gte=today,
    #     status="Approved"
    #       ).first()

    #     if approved_leave:
    #     # ✅ If employee punches in, mark the leave as not taken
    #      approved_leave.status = "Not Taken"
    #      approved_leave.save()

    #      # (Optional) Log or notify
    #      NotificationLog.objects.create(
    #          user=user,
    #          action=f"Leave on {today} marked as 'Not Taken' due to punch-in.",
    #          title="Leave Updated"
    #      )
        
    #     active_punch_in = Attendance.objects.filter(
    #         employee=employee,
    #         date=today,
    #         out_time__isnull=True,  # means still active
    #         punch_in=True
    #     ).first()

    #     if active_punch_in:
    #         return Response({
    #             "success": False,
    #             "message": "You already have an active punch-in. Please punch-out first."
    #         }, status=400)
        
    #     today_punch_count = Attendance.objects.filter(employee=employee, date=today).count()

    #     # Mark attendance
    #     user = employee.user
    #     # Convert punch-in time to IST
    #     ist = pytz.timezone("Asia/Kolkata")
    #     in_time_utc = timezone.now()
    #     in_time_ist = in_time_utc.astimezone(ist)

    #     late_threshold = time(9, 40) 
    # # Check for late
    #     if today_punch_count == 0:
    #         if in_time_ist.time() > late_threshold:
    #             status_value = "Late"
    #             NotificationLog.objects.create(
    #                 user=user,
    #                 action=f"Late punch-in recorded today at {in_time_ist.strftime('%H:%M:%S')}",
    #                 title = status_value,
    #             )
    #         else:
    #             status_value = "Present"
    #     else:
    #     # For subsequent punch-ins, don't mark as late or create notification
    #      status_value = "Present"


    #     Attendance.objects.create(
    #         employee=employee,
    #         date=timezone.now().date(),
    #         in_time=timezone.now(),
    #         attendance_type="WFH",
    #         status="Present",
    #         location=f"{latitude},{longitude}",
    #         selfie=image_file,
    #         verified_by=user,
    #     )

    #     return Response({
    #         "success": True,
    #         "message": "Face matched and check-in recorded",
    #         "confidence": confidence,
    #         "employee": EmployeeSerializer(employee).data,
    #         "attendance_type": "WFH",
    #         "on-site": False,
    #         "user": UserLoginSerializer(user).data,
           
    #     })
    


# face log out api - punch out
class FaceLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print(decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data

        user_id = data.get("user_id")
        image_file = request.FILES.get("image")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not user_id or not image_file:
            return Response({"success": False, "error": "user_id and image are required"}, status=400)

        employee = get_object_or_404(EmployeeDetail, user__id=user_id)

        # ------------------------------
        # 1️⃣ Ensure employee face encoding exists
        # ------------------------------
        if not employee.face_encoding:
            if not employee.profile_pic:
                return Response({"success": False, "error": "No profile picture found"}, status=404)
            
            profile_embedding = generate_face_embedding(employee.profile_pic.path)
            if not profile_embedding:
                return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
            
            employee.face_encoding = profile_embedding
            employee.save()

        # ------------------------------
        # 2️⃣ Generate embedding from uploaded logout selfie
        # ------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in image_file.chunks():
                tmp_file.write(chunk)
            uploaded_path = tmp_file.name

        uploaded_embedding = generate_face_embedding(uploaded_path)
        os.remove(uploaded_path)

        if not uploaded_embedding:
            return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)

        # Convert stored encoding to numpy arrays
        stored_encoding = np.array(employee.face_encoding)
        uploaded_encoding = np.array(uploaded_embedding)

        # ------------------------------
        # 3️⃣ Compare embeddings — stricter threshold
        # ------------------------------
        match, confidence = compare_faces(stored_encoding, uploaded_encoding, threshold=0.8)

        if not match:
            return Response({
                "success": False,
                "error": "Face does not match. Logout verification failed.",
                "confidence": confidence
            }, status=401)

        # ------------------------------
        # 4️⃣ Find today's active attendance record
        # ------------------------------
        attendance = Attendance.objects.filter(
            employee=employee,
            date=timezone.localdate(),
            out_time__isnull=True
        ).last()

        if not attendance:
            return Response({"success": False, "error": "No active attendance record found."}, status=404)

        # ------------------------------
        # 5️⃣ Update attendance with logout info
        # ------------------------------
        attendance.out_time = timezone.now()
        attendance.out_selfie = image_file  # ✅ store logout selfie separately
        attendance.location = f"{latitude},{longitude}" if latitude and longitude else attendance.location
        attendance.save()

        # ------------------------------
        # 6️⃣ Return successful response
        # ------------------------------
        return Response({
            "success": True,
            "message": "Face matched and logout recorded",
            "confidence": confidence,
            "attendance": {
                "date": attendance.date.strftime("%Y-%m-%d"),
                "in_time": attendance.in_time.astimezone().strftime("%H:%M:%S"),
                "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S"),
                "location": f"{latitude},{longitude}",
                "employee": EmployeeSerializer(employee).data
            }
        })


    # def post(self, request):
    #     user_id = request.data.get("user_id")
    #     image_file = request.FILES.get("image")
    #     latitude = request.data.get("latitude")
    #     longitude = request.data.get("longitude")

    #     if not user_id or not image_file:
    #         return Response({"success": False, "error": "user_id and image are required"}, status=400)
    #     print("DATA:", request.data)
    #     print("FILES:", request.FILES)


    #     employee = get_object_or_404(EmployeeDetail, user__id=user_id)

    #     if employee.face_encoding is None:
    #         if not employee.profile_pic:
    #             return Response({"success": False, "error": "No profile picture found"}, status=404)
            
    #         profile_embedding = generate_face_embedding(employee.profile_pic.path)
    #         if profile_embedding is None:
    #             return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
    #         employee.face_encoding = profile_embedding.tolist()
    #         employee.save()

    #     # Save uploaded logout image temporarily to generate embedding
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
    #         for chunk in image_file.chunks():
    #             tmp_file.write(chunk)
    #         uploaded_path = tmp_file.name

    #     uploaded_embedding = generate_face_embedding(uploaded_path)
    #     os.remove(uploaded_path)

    #     if uploaded_embedding is None:
    #         return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)

    #     # Compare embeddings
    #     match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.5)
    #     if not match:
    #         return Response({
    #             "success": False,
    #             "error": "Face does not match",
    #             "confidence": confidence
    #         }, status=401)

    #     # Find active attendance record
    #     attendance = Attendance.objects.filter(
    #         employee=employee,
    #         date=timezone.now().date(),
    #         out_time__isnull=True
    #     ).last()

    #     if not attendance:
    #         return Response({"success": False, "error": "No active attendance found"}, status=404)

    #     attendance.out_time = timezone.now()
    #     attendance.save()

    #     return Response({
    #         "success": True,
    #         "message": "Face matched and logout recorded",
    #         "confidence": confidence,
    #         "attendance": {
    #             "date": attendance.date.strftime("%Y-%m-%d"),
    #             "in_time": attendance.in_time.astimezone().strftime("%H:%M:%S"),
    #             "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S"),
    #             "location": f"{latitude},{longitude}",
    #             "employee": EmployeeSerializer(employee).data
    #         }
    #     })
    




# class QRSessionCreateAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         # Only allow admins (or whoever you want)
#         if request.user.role != "employee":
#             return Response(
#                 {"status": "failed", "message": "Unauthorized"},
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         try:
#             latitudes = float(request.data.get("latitudes"))
#             longitude = float(request.data.get("longitude"))
#         except (TypeError, ValueError):
#             return Response(
#                 {"status": "failed", "message": "Invalid latitude/longitude"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Generate a random code for QR
#         code = get_random_string(length=12)

#         qr_session = QR_Session.objects.create(
#             code=code,
#             latitudes=latitudes,
#             longitude=longitude
#         )

#         # Generate QR image
#         qr = qrcode.make(code)
#         buffer = io.BytesIO()
#         qr.save(buffer, format="PNG")
#         qr_base64 = base64.b64encode(buffer.getvalue()).decode()

#         return Response(
#             {
#                 "status": "success",
#                 "message": "QR Session created",
#                 "qr_code": code,  # the actual string scanned by employees
#                 "qr_image_base64": qr_base64,  # frontend can render this
#                 "latitude": qr_session.latitudes,
#                 "longitude": qr_session.longitude,
#             },
#             status=status.HTTP_201_CREATED,
#         )

import secrets
from django.utils.crypto import RANDOM_STRING_CHARS

def generate_qr_string(length=12, prefix="HYBRID-ATTENDANCE-QR-", allowed_chars=RANDOM_STRING_CHARS):
    random_part = "".join(secrets.choice(allowed_chars) for _ in range(length))
    return f"{prefix}{random_part}"

class QRSessionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Leave Request:", decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data

        # Only allow employees (or restrict to admin if needed)
        if request.user.role != "employee":
            return Response(
                {"status": "failed", "message": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            latitudes = float(request.data.get("latitudes"))
            longitude = float(request.data.get("longitude"))
        except (TypeError, ValueError):
            return Response(
                {"status": "failed", "message": "Invalid latitude/longitude"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate a random code for QR
        code = generate_qr_string(12)

        qr_session = QR_Session.objects.create(
            code=code,
            latitudes=latitudes,
            longitude=longitude
        )

        # Generate QR image
        qr = qrcode.make(code)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")

        # Return PNG file directly
        response = HttpResponse(buffer.getvalue(), content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="qr_{qr_session.id}.png"'
        return response        

# def calculate_distance(lat1, lon1, lat2, lon2):
#     R = 63701000  
#     d_lat = radians(lat2 - lat1)
#     d_lon = radians(lon2 - lon1)
#     a = sin(d_lat/2) ** -2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon/2) ** 2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
#     return R * c
from math import radians, sin, cos, sqrt, atan2
import pytz

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters (use 6,371,000 not 63,701,000!)
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# @api_view(["POST"])
# # @parser_classes([MultiPartParser, FormParser])
# @permission_classes([IsAuthenticated])
# def  punch_in_view(request):
#     print(request.data) 
#     decrypted_data = decrypt_request_payload(request)

#     if decrypted_data:
#             print("Decrypted Request:", decrypted_data)
#             # Replace request.data with decrypted version
#             data = decrypted_data
#     else:
#             print("Normal  Request:", request.data)
#             data = request.data

#     user = request.user

#     # if user.role != "employee":
#     #     return JsonResponse({"status": "failed", "message": "Only employees can punch-in"}, status=403)

#     try:
#         employee = user.employee_profile
#     except EmployeeDetail.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)

#     # data = request.data
#     qr_code = data.get("qr_code")

#     lat_value = data.get("latitude") or data.get("phone_lat")
#     lon_value = data.get("longitude") or data.get("phone_lon")
#     if lat_value is None or lon_value is None:
#         return JsonResponse({"status": "failed", "message": "Latitude and Longitude are required"}, status=400)

#     phone_lat = float(lat_value)
#     phone_lon = float(lon_value)
#     ALLOWED_PREFIX = "HYBRID-ATTENDANCE-QR-"

#     if not qr_code or not qr_code.startswith(ALLOWED_PREFIX):
#         return JsonResponse({
#             "status": "failed",
#             "message": "Invalid QR Code (Only Attendance App QR allowed)"
#         }, status=400)

#     try:
#         # if not qr_code.startswith("OFFICE-QR-"):
#           qrsession = QR_Session.objects.get(code=qr_code)
#     except QR_Session.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Invalid QR Code"}, status=400)

#     distance = calculate_distance(phone_lat, phone_lon, qrsession.latitudes, qrsession.longitude)
#     if distance > 500:  # meters
#         return JsonResponse({"status": "failed", "message": "Location mismatch!"}, status=400)

#     today = timezone.now().date()

#      # ✅ Check if employee has approved leave for today
#     approved_leave = Leave.objects.filter(
#         employee=employee,
#         start_date__lte=today,
#         end_date__gte=today,
#         status="Approved"
#     ).first()

#     if approved_leave:
#         # ✅ If employee punches in, mark the leave as not taken
#         approved_leave.status = "Not Taken"
#         approved_leave.save()

#         # (Optional) Log or notify
#         NotificationLog.objects.create(
#             user=user,
#             action=f"Leave on {today} marked as 'Not Taken' due to punch-in.",
#             title="Leave Updated"
#         )

#     # Check for active punch-in
#     active_punch_in = Attendance.objects.filter(
#         employee=employee,
#         date=today,
#         out_time__isnull=True,
#         punch_in=True
#     ).first()
#     if active_punch_in:
#         return JsonResponse({
#             "status": "failed",
#             "message": "You have an active punch-in session. Please punch-out first."
#         }, status=400)

#     # Count total punch-ins for today
#     today_punch_count = Attendance.objects.filter(employee=employee, date=today).count()

#     # Convert punch-in time to IST
#     ist = pytz.timezone("Asia/Kolkata")
#     in_time_utc = timezone.now()
#     in_time_ist = in_time_utc.astimezone(ist)
    
#     late_threshold = time(9, 40) 
#     # Check for late
#     # if today_punch_count == 0:
#     #     if in_time_ist.time() > late_threshold:
#     #         status_value = "Late"
#     #         NotificationLog.objects.create(
#     #             user=user,
#     #             action=f"Late punch-in recorded today at {in_time_ist.strftime('%H:%M:%S')}",
#     #             title = "Late"
#     #         )
#     #     else:
#     #         status_value = "Present"
#     # else:
#     #     # For subsequent punch-ins, don't mark as late or create notification
#     #     status_value = "Present"
#     # Get Employee Shift Start Time
#     shift = employee.employee_shift
#     if not shift:
#         shift_start = time(9, 40)  # default 9:40
#     else:
#         shift_start = shift.relaxation_start

#     # Normalize seconds
#     punch_time = in_time_ist.time().replace(second=0, microsecond=0)
#     shift_start = shift_start.replace(second=0, microsecond=0)

#     # Determine status
#     if today_punch_count == 0:  # first punch only
#         if punch_time > shift_start:
#             status_value = "Late"
#             NotificationLog.objects.create(
#                 user=user,
#                 action=f"Late punch-in. Shift start: {shift_start}, punched at {in_time_ist.strftime('%H:%M:%S')}",
#                 title="Late"
#             )
#         else:
#             status_value = "Present"
#     else:
#         status_value = "Present"

#     # if today_punch_count == 0:
#     #     if in_time_ist.time() > shift_start:
#     #         status_value = "Late"
#     #         NotificationLog.objects.create(
#     #             user=user,
#     #             action=f"Late punch-in. Shift start: {shift_start}, punched at {in_time_ist.strftime('%H:%M:%S')}",
#     #             title="Late"
#     #         )
#     #     else:
#     #         status_value = "Present"
#     # else:
#     #     status_value = "Present"


#     # Create Attendance record
#     attendance = Attendance.objects.create(
#         employee=employee,
#         date=today,
#         in_time=in_time_utc,
#         attendance_type="office",
#         location=f"{phone_lat},{phone_lon}",
#         qr_scan=True,
#         qrsession=qrsession,
#         status=status_value,
#         punch_in=True
#     )

#     return JsonResponse({
#         "status": "success",
#         "message": "Punch-in successful",
#         "employee_id": employee.employee_id,
#         "attendance_type": "office",
#         "on-site": True,
#         "in_time": in_time_ist.strftime("%H:%M:%S"),
#         "punch_session": today_punch_count + 1,
#         "total_sessions_today": today_punch_count + 1,
#         "status_value": status_value
#     })


# # logout  api punch out 
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def punch_out(request):
#     print(request.data)
#     decrypted_data = decrypt_request_payload(request)

#     data = decrypted_data if decrypted_data else request.data

#     user = request.user

#     # if user.role != "employee":
#     #     return JsonResponse({"status": "failed", "message": "Only employees can punch-out"}, status=403)

#     try:
#         employee = user.employee_profile
#     except EmployeeDetail.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)



#     qr_code = data.get("qr_code")
#     lat_value = data.get("latitude") or data.get("phone_lat")
#     lon_value = data.get("longitude") or data.get("phone_lon")

#     if lat_value is None or lon_value is None:
#         return JsonResponse({"status": "failed", "message": "Latitude and Longitude are required"}, status=400)

#     phone_lat = float(lat_value)
#     phone_lon = float(lon_value)


#     ALLOWED_PREFIX = "HYBRID-ATTENDANCE-QR-"

#     if not qr_code or not qr_code.startswith(ALLOWED_PREFIX):
#         return JsonResponse({
#             "status": "failed",
#             "message": "Invalid QR Code (Only Attendance App QR allowed)"
#         }, status=400)


#     try:
#         qrsession = QR_Session.objects.get(code=qr_code)
#     except QR_Session.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Invalid QR Code"}, status=400)


#     distance = calculate_distance(phone_lat, phone_lon, qrsession.latitudes, qrsession.longitude)
#     if distance > 500:  # meters
#         return JsonResponse({"status": "failed", "message": "Location mismatch!"}, status=400)


#     today = timezone.now().date()

#     attendance = Attendance.objects.filter(
#         employee=employee,
#         date=today,
#         out_time__isnull=True,
#         punch_in=True
#     ).order_by('-in_time').first()

#     if not attendance:
#         return JsonResponse({"status": "failed", "message": "No active punch-in found"}, status=400)

#     # Calculate session duration
#     session_duration = timezone.now() - attendance.in_time
#     duration_hours = session_duration.total_seconds() / 3600

#     attendance.out_time = timezone.now()
#     attendance.punch_in = False
#     attendance.save()

#     completed_sessions = Attendance.objects.filter(
#         employee=employee,
#         date=today,
#         out_time__isnull=False
#     ).count()

#     return JsonResponse({
#         "status": "success",
#         "message": "Punch-out successful",
#         "employee_id": employee.employee_id,
#         "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S"),
#         "session_duration_hours": round(duration_hours, 2),
#         "completed_sessions_today": completed_sessions
#     })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def punch_in_view(request):
    user = request.user

    # Role check
    if user.role != "employee":
        return JsonResponse({"status": "failed", "message": "Only employees can punch-in"}, status=403)

    # Employee profile
    try:
        employee = user.employee_profile
    except EmployeeDetail.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)

    data = request.data
    qr_code = data.get("qr_code")

    # Geo location check
    lat_value = data.get("latitude") or data.get("phone_lat")
    lon_value = data.get("longitude") or data.get("phone_lon")

    if lat_value is None or lon_value is None:
        return JsonResponse({"status": "failed", "message": "Latitude & Longitude required"}, status=400)
                                                                                                                                                                                                                      
    try:
        phone_lat = float(lat_value)
        phone_lon = float(lon_value)
    except (TypeError, ValueError):
        return JsonResponse({"status": "failed", "message": "Invalid latitude/longitude"}, status=400)

    # QR Validations
    try:
        qrsession = QR_Session.objects.get(code=qr_code)
    except QR_Session.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Invalid QR Code"}, status=400)

    qrs_lat = getattr(qrsession, "latitude", None) or getattr(qrsession, "latitudes", None)
    qrs_lon = getattr(qrsession, "longitude", None) or getattr(qrsession, "longitudes", None) or getattr(qrsession, "lon", None)

    distance = calculate_distance(phone_lat, phone_lon, float(qrs_lat), float(qrs_lon))
    if distance > 500:
        return JsonResponse({"status": "failed", "message": "Location mismatch!"}, status=400)

    # Date (IST)
    ist = pytz.timezone("Asia/Kolkata")
    now_utc = timezone.now()
    now_ist = now_utc.astimezone(ist)
    today_ist = now_ist.date()

    # Leave Auto Update
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

    # Already Active Punch Check
    active_punch = Attendance.objects.filter(
        employee=employee,
        date=today_ist,
        punch_in=True,
        out_time__isnull=True
    ).first()

    if active_punch:
        return JsonResponse({
            "status": "failed",
            "message": "You already punched-in. Please punch-out."
        }, status=400)

    # Shift check
    shift = employee.employee_shift
    if not shift:
        return JsonResponse({"status": "failed", "message": "Shift not assigned"}, status=400)

    start = shift.start_time
    start_dt = ist.localize(datetime.combine(today_ist, start))
    present_end_dt = start_dt + timedelta(minutes=15)

    punch_dt = now_ist

    # Night shift rule
    if start > shift.relaxation_end:
        present_end_dt += timedelta(days=1)
        if punch_dt.time() < start:
            punch_dt = punch_dt + timedelta(days=1)

    # -----------------------------------------
    # FINAL ATTENDANCE STATUS + NOTIFICATIONS
    # -----------------------------------------
    if punch_dt < start_dt:
        status_value = "Early Punch-in"
        NotificationLog.objects.create(
            user=user,
            title="Early Punch-in",
            action=f"Early punch-in. Scheduled time: {start.strftime('%H:%M:%S')}, punched at {now_ist.strftime('%H:%M:%S')}"
        )

    elif start_dt <= punch_dt <= present_end_dt:
        status_value = "Present"
        
    else:
        status_value = "Late Punch-in"
        NotificationLog.objects.create(
            user=user,
            title="Late Punch-in",
            action=f"Late punch-in. Shift start: {start.strftime('%H:%M:%S')}, punched at {now_ist.strftime('%H:%M:%S')}"
        )

    # Create Attendance
    attendance = Attendance.objects.create(
        employee=employee,
        date=today_ist,
        in_time=now_utc,
        attendance_type="office",
        location=f"{phone_lat},{phone_lon}",
        qr_scan=True,
        qrsession=qrsession,
        status=status_value,
        punch_in=True
    )

    return JsonResponse({
        "status": "success",
        "message": "Punch-in successful",
        "attendance_status": status_value,
        "in_time": now_ist.strftime("%H:%M:%S"),
        "shift": shift.shifts_name,
        "session_count": Attendance.objects.filter(employee=employee, date=today_ist).count()
    })










@api_view(["POST"])
@permission_classes([IsAuthenticated])
def punch_out(request):

    user = request.user

    # -------------------------------
    # Role Check
    # -------------------------------
    if user.role != "employee":
        return JsonResponse({"status": "failed", "message": "Only employees can punch-out"}, status=403)

    # -------------------------------
    # Employee Profile
    # -------------------------------
    try:
        employee = user.employee_profile
    except EmployeeDetail.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)

    # -------------------------------
    # Current UTC + IST
    # -------------------------------
    now_utc = timezone.now()
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = now_utc.astimezone(ist)

    # -------------------------------
    # Active Attendance Record
    # -------------------------------
    attendance = Attendance.objects.filter(
        employee=employee,
        out_time__isnull=True,
        punch_in=True
    ).order_by('-in_time').first()

    if not attendance:
        return JsonResponse({"status": "failed", "message": "No active punch-in found"}, status=400)

    # -------------------------------
    # Shift Details
    # -------------------------------
    shift = getattr(employee, "employee_shift", None)
    if not shift:
        return JsonResponse({"status": "failed", "message": "Shift not assigned"}, status=400)

    start_time = shift.start_time
    end_time = shift.end_time

    in_time_ist = attendance.in_time.astimezone(ist)
    base_date = in_time_ist.date()

    # Build aware start/end datetimes
    start_dt = ist.localize(datetime.combine(base_date, start_time))
    end_dt = ist.localize(datetime.combine(base_date, end_time))

    # Shift crosses midnight
    if end_time <= start_time:
        end_dt += timedelta(days=1)
        if in_time_ist.time() <= end_time:
            start_dt = ist.localize(datetime.combine(base_date - timedelta(days=1), start_time))
            end_dt = ist.localize(datetime.combine(base_date, end_time))

    # 6 hours buffer after shift end
    six_hours_after_end = end_dt + timedelta(hours=6)

    # -------------------------------
    # Punch-out Status
    # -------------------------------
    if now_ist < end_dt:
        punchout_status = "Early Punch-out"
    elif end_dt <= now_ist <= six_hours_after_end:
        punchout_status = "Punch-out"  # NORMAL
    else:
        punchout_status = "Late Punch-out"

    # -------------------------------
    # Save Punch-out
    # -------------------------------
    duration = now_utc - attendance.in_time
    attendance.out_time = now_utc
    attendance.punch_in = False
    attendance.punchout_status = punchout_status
    attendance.save()

    # -------------------------------
    # Notification Logic
    # -------------------------------
    # SAVE ONLY FOR: Early Punch-out & Late Punch-out  
    # DO NOT SAVE FOR NORMAL Punch-out  
    if punchout_status != "Punch-out":  
        NotificationLog.objects.create(
            user=user,
            title=punchout_status,
            action=f"{punchout_status}. Shift end: {end_dt.strftime('%H:%M:%S')}, "
                   f"punched out at {now_ist.strftime('%H:%M:%S')}"
        )

    # -------------------------------
    # Count Completed Sessions Today
    # -------------------------------
    attendance_date_ist = in_time_ist.date()
    start_range = ist.localize(datetime.combine(attendance_date_ist, datetime.min.time())).astimezone(pytz.UTC)
    end_range = ist.localize(datetime.combine(attendance_date_ist, datetime.max.time())).astimezone(pytz.UTC)

    completed_sessions = Attendance.objects.filter(
        employee=employee,
        out_time__isnull=False,
        in_time__gte=start_range,
        in_time__lte=end_range
    ).count()

    # -------------------------------
    # Response
    # -------------------------------
    return JsonResponse({
        "status": "success",
        "message": "Punch-out successful",
        "shift": shift.shifts_name,
        "punchout_status": punchout_status,
        "out_time": now_ist.strftime("%H:%M:%S"),
        "session_duration_hours": round(duration.total_seconds() / 3600.0, 2),
        "completed_sessions_today": completed_sessions
    })




