from django.utils import timezone
from django.core.mail import send_mail
from datetime import datetime
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, EmployeeDetail, EmailOTP, NotificationLog
from .serializers import UserLoginSerializer, EmployeeSerializer
import random
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.generics import ListAPIView
from django.core.mail import send_mail
from .models import User, EmailOTP
import random
import hashlib
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import time
from rest_framework.permissions import BasePermission
from . serializers import *
import qrcode
from django.db.models import Min, Max
from web_app.serializers import *
import io
import base64
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
import json
from django.http import JsonResponse
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
from . models import *
import holidays as pyholidays
from datetime import date, datetime
from django.db.models import F, ExpressionWrapper, fields, Sum


# -----------------------------
# Utility
# -----------------------------
def generate_otp():
    return str(random.randint(1000, 9999))


# -----------------------------
# Login View
# -----------------------------


class LoginView(APIView):
    permission_classes = [AllowAny]


    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"success": False, "message": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)  # ✅ custom User
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password):
            return Response(
                {"success": False, "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"success": False, "message": "Account is inactive. Contact admin."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------
        # Role → Privileges mapping
        # ----------------------------
        if user.role == "superadmin":
            privileges = ["superadmin"]
        elif user.role == "admin":
            privileges = ["admin", "employee"]  # ✅ team lead = both
        else:
            privileges = ["employee"]

        try:
            employee_id = user.employee_profile.employee_id
        except Exception:
            employee_id = None      

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role  # include role in token
        refresh["user_id"] = user.id     

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "employee_id": employee_id,
                    "privileges": privileges,
                    
                },

                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )



# check whether the user in logged in or not 
class CheckLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "message": "User is already logged in",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        })


# -----------------------------
# refreshing token api 
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify & decode refresh token
            old_refresh = RefreshToken(refresh_token)
            user_id = old_refresh.get("user_id")

            # Fetch user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"success": False, "message": "User not found"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Issue new refresh + access
            new_refresh = RefreshToken.for_user(user)
            new_refresh["role"] = user.role
            new_refresh["user_id"] = user.id

            return Response(
                {
                    "success": True,
                    "message": "Token refreshed successfully",
                    "access": str(new_refresh.access_token),
                    "refresh": str(new_refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {"success": False, "message": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# -----------------------------
# Forgot Password (OTP)
# -----------------------------


# Utility to generate OTP and hash
def generate_otp():
    # Generate 4-digit OTP
    otp = str(random.randint(1000, 9999))  # 1000-9999 → 4 digits
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    return otp, otp_hash

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"success": False, "error": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "error": "Email not found"}, status=404)

        otp, otp_hash = generate_otp()
        expiry = timezone.now() + timezone.timedelta(minutes=10)

        EmailOTP.objects.create(user=user, otp_hash=otp_hash, purpose="reset_password", expires_at=expiry)

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP for password reset is: {otp}",
            from_email="no-reply@example.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"success": True, "message": "OTP sent to your email"}, status=200)


# resend otp view
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"success": False, "error": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "error": "Email not found"}, status=404)

        otp, otp_hash = generate_otp()
        expiry = timezone.now() + timezone.timedelta(minutes=10)

        EmailOTP.objects.create(user=user, otp_hash=otp_hash, purpose="resend-otp", expires_at=expiry)

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP for password reset is: {otp}",
            from_email="no-reply@example.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"success": True, "message": "OTP re-sent to your email"}, status=200)

# -----------------------------
# Verify OTP
# -----------------------------
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"success": False, "error": "Email and OTP are required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "error": "Invalid email"}, status=404)

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        otp_record = EmailOTP.objects.filter(
            user=user,
            otp_hash=otp_hash,
            is_used=False,
            purpose="reset_password",
            expires_at__gte=timezone.now()
        ).last()

        if not otp_record:
            return Response({"success": False, "error": "OTP invalid or expired"}, status=400)

        otp_record.is_used = True
        otp_record.is_verified = True  # ✅ mark verified
        otp_record.save()

        return Response({"success": True, "message": "OTP verified successfully"}, status=200)
# -----------------------------
# Reset Password
# -----------------------------
from django.contrib.auth.hashers import make_password

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")

        if not email or not new_password:
            return Response({"success": False, "error": "Email and new password are required"}, status=400)

        try:
            user = User.objects.get(email=email)
            otp_record = EmailOTP.objects.filter(user=user, purpose="reset_password", is_verified=True).last()
            if not otp_record:
                return Response({"success": False, "error": "OTP not verified"}, status=400)
        except User.DoesNotExist:
            return Response({"success": False, "error": "Invalid email"}, status=404)
        
        # check if old password and new password are same
        if check_password(new_password, user.password):
            return Response({"success": False, "error": "New password cannot be the same as the old password"}, status=400)
        user.password = make_password(new_password)
        user.save()

        return Response({"success": True, "message": "Password reset successfully"}, status=200)






# -----------------------------
# Profile
# -----------------------------
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Role → Privileges mapping
        if user.role == "superadmin":
            privileges = ["superadmin"]
        elif user.role == "admin":
            privileges = ["admin", "employee"]
        else:
            privileges = ["employee"]

        return Response(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "privileges": privileges,
                    "isOnline": True  # 👈 can replace with real logic later
                }
            },
            status=status.HTTP_200_OK
        )


# employee detail view
class EmployeeProfileView(APIView):
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        try:
            employee = EmployeeDetail.objects.get(user=request.user)
        except EmployeeDetail.DoesNotExist:
            return Response({"success": False, "message": "Employee profile not found"}, status=404)

        serializer = EmployeeDetailSerializer(employee)
        return Response({
            "success": True,
            "employee": serializer.data
        }, status=200)

# -----------------------------
# Notification
# -----------------------------
class NotificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread = NotificationLog.objects.filter(user=request.user).count()
        return Response({'unreadCount': unread})


# -----------------------------
# Employee Registration
# -----------------------------


# -----------------------------
# Custom Permission
# -----------------------------
# class IsAdminOrSuperadmin(BasePermission):
#     """
#     Only users with role = admin or superadmin can register employees.
#     """
#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated
#             and hasattr(request.user, "role")
#             and request.user.role in ["admin", "superadmin"]
#         )

# -----------------------------
# Employee Registration View
# -----------------------------
class EmployeeRegistrationView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmployeeSerializer(data=request.data)

        if serializer.is_valid():
            employee = serializer.save()
            user = employee.user  # linked User object

            # ----------------------------
            # Role → Privileges mapping
            # ----------------------------
            if user.role == "superadmin":
                privileges = ["superadmin"]
            elif user.role == "admin":
                privileges = ["admin", "employee"]  # ✅ team lead has both
            else:
                privileges = ["employee"]

            return Response(
                {
                    "success": True,
                    "message": "Employee registered successfully",
                    "employee": {
                        "id": employee.id,
                        "firstName": employee.first_name,
                        "lastName": employee.last_name,
                        "user_type": employee.user_type,
                        "job_type": employee.job_type,
                        "employeeId": employee.employee_id,
                        "department": employee.department,
                        "designation": employee.designation,
                        "repMgrTl": employee.reporting_manager,  # ✅ now plain text
                        "salary": str(employee.salary) if employee.salary else None,
                        "phone": employee.phone,
                        "address": employee.address,
                        "dob": employee.dob,
                        "gender": employee.gender,
                        "nationality": employee.nationality,
                        "bloodGroup": employee.blood_group,
                        "emergencyContact": employee.emergency_contact,
                        "profilePic": request.build_absolute_uri(employee.profile_pic.url) if employee.profile_pic else None,
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "role": user.role,
                            "privileges": privileges
                        }
                    }
                },
                status=status.HTTP_201_CREATED
            )

        # ❌ Validation errors
        return Response(
            {"success": False, 
             "errors": serializer.errors
             },
            status=status.HTTP_400_BAD_REQUEST
        )





# import numpy as np

# Try to import face_recognition, but don't fail if it's not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition module not available. Face verification features will be disabled.")
# Try to import DeepFace, but don't fail if it's not available (avoids cv2 DLL crash at import time)
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except Exception as deepface_import_error:
    DEEPFACE_AVAILABLE = False
    print(f"Warning: DeepFace not available. Face verification features will be disabled. Reason: {deepface_import_error}")
# from geopy.geocoders import Nominatim
from datetime import timedelta

from .models import EmployeeDetail, Attendance
from .serializers import EmployeeSerializer, UserLoginSerializer

# def format_timedelta(td):
#     total_seconds = int(td.total_seconds())
#     hours = total_seconds // 3600
#     minutes = (total_seconds % 3600) // 60
#     return f"{hours:02d}:{minutes:02d}"
# def generate_face_encoding(image_path):
#     if not FACE_RECOGNITION_AVAILABLE:
#         print("Face recognition not available - cannot generate face encoding")
#         return None
    
#     try:
#         images = face_recognition.load_image_file(image_path)
#         encodings = face_recognition.face_encodings(images)
#         if encodings:
#             return encodings[0].tolist()  
#         return None
#     except Exception as e:
#         print("Error generating face encoding:", e)
#         return None



# class FaceVerifyView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         if not FACE_RECOGNITION_AVAILABLE:
#             return Response({
#                 "success": False, 
#                 "error": "Face recognition feature is not available. Please install face_recognition package."
#             }, status=503)

#         user_id = request.data.get("user_id")
#         image_file = request.FILES.get("image")
#         latitude = request.data.get("latitude")
#         longitude = request.data.get("longitude")

#         if not user_id or not image_file:
#             return Response({"success": False, "error": "user_id and image are required"}, status=400)

#         employee = get_object_or_404(EmployeeDetail, user_id=user_id)

#         if not employee.profile_pic:
#             return Response({"success": False, "error": "No profile picture found"}, status=404)

#         if not employee.face_encoding:
#             profileencoding = generate_face_encoding(employee.profile_pic.path)
#             if not profileencoding:
#                 return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
#             employee.face_encoding = profileencoding
#             employee.save()

#         uploaded_image = face_recognition.load_image_file(image_file)
#         uploaded_encodings = face_recognition.face_encodings(uploaded_image)
#         if not uploaded_encodings:
#             return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)
#         uploaded_encoding = uploaded_encodings[0]

#         registered_encoding = np.array(employee.face_encoding)
#         distance = face_recognition.face_distance([registered_encoding], uploaded_encoding)[0]
#         confidence = round((1 - distance) * 100, 2)
#         THRESHOLD = 0.4 

#         if distance >= THRESHOLD:
#             return Response({"success": False, "error": "Face does not match", "confidence": confidence}, status=401)

#         user = employee.user
#         refresh = RefreshToken.for_user(user)

#         Attendance.objects.create(
#             employee=employee,
#             date=timezone.now().date(),
#             in_time=timezone.now(),
#             attendance_type="office",
#             status="Present",
#             latitude=latitude,
#             longitude=longitude,
#             selfie=image_file,
#             verified_by=user,
#         )

#         return Response({
#             "success": True,
#             "message": "Face matched and check-in recorded",
#             "confidence": confidence,
#             "employee": EmployeeSerializer(employee).data,
#             "user": UserLoginSerializer(user).data,
#             "tokens": {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }
#         })
# DeepFace import is handled above with try/except
from django.http import HttpResponse

# def format_timedelta(td):
#     total_seconds = int(td.total_seconds())
#     hours = total_seconds // 3600
#     minutes = (total_seconds % 3600) // 60
#     return f"{hours:02d}:{minutes:02d}"

# class FaceVerifyView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         user_id = request.data.get("user_id")
#         image_file = request.FILES.get("image")
#         latitude = request.data.get("latitude")
#         longitude = request.data.get("longitude")

#         if not user_id or not image_file:
#             return Response({"success": False, "error": "user_id and image are required"}, status=400)

#         employee = get_object_or_404(EmployeeDetail, user_id=user_id)

#         if not employee.profile_pic:
#             return Response({"success": False, "error": "No profile picture found"}, status=404)

#         try:
#             result = DeepFace.verify(
#                 img1_path=employee.profile_pic.path,
#                 img2_path=image_file,
#                 model_name='Facenet',  # You can use 'VGG-Face', 'ArcFace', etc.
#                 enforce_detection=True
#             )
#         except Exception as e:
#             return Response({"success": False, "error": f"Face verification failed: {str(e)}"}, status=400)

#         if not result['verified']:
#             return Response({"success": False, "error": "Face does not match", "confidence": round(result['distance']*100, 2)}, status=401)

#         user = employee.user
#         refresh = RefreshToken.for_user(user)

#         Attendance.objects.create(
#             employee=employee,
#             date=timezone.now().date(),
#             in_time=timezone.now(),
#             attendance_type="office",
#             status="Present",
#             latitude=latitude,
#             longitude=longitude,
#             selfie=image_file,
#             verified_by=user,
#         )

#         return Response({
#             "success": True,
#             "message": "Face matched and check-in recorded",
#             "confidence": round((1 - result['distance'])*100, 2),
#             "employee": EmployeeSerializer(employee).data,
#             "user": UserLoginSerializer(user).data,
#             "tokens": {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }
#         })
    
# try:
    

#     from PIL import Image
#     import numpy as np
#     import insightface
#     from PIL import Image

#     face_app = insightface.app.FaceAnalysis(name="buffalo_l")
#     face_app.prepare(ctx_id=0, det_size=(640, 640))  # Only numpy arrays
#     FACE_PACKAGES_AVAILABLE = True
#     print("✅ InsightFace loaded without OpenCV")

# except Exception as e:
#     print("⚠️ InsightFace not available:", e)
#     face_app = None
#     FACE_PACKAGES_AVAILABLE = False


# def generate_face_embedding(image_path):
#     """
#     Generate face embedding using InsightFace without cv2
#     """
#     if not FACE_PACKAGES_AVAILABLE or not face_app:
#         print("⚠️ InsightFace not available")
#         return None

#     try:
#         img = Image.open(image_path).convert("RGB")  # Pillow handles image loading
#         img = np.array(img)                          # Convert to numpy array
#         faces = face_app.get(img)                    # InsightFace works on numpy array
#         print(f"Detected {len(faces)} faces in {image_path}")

#         if not faces:
#             return None

#         face = max(faces, key=lambda f: f.bbox[2] - f.bbox[0])  # largest face
#         return face.embedding.tolist()

#     except Exception as e:
#         print("❌ Error generating face embedding:", e)
#         return None



# def compare_faces(known_embedding, uploaded_embedding, threshold=0.5):
#     """
#     Compare two embeddings using cosine similarity
#     """
#     known_vec = np.array(known_embedding)
#     uploaded_vec = np.array(uploaded_embedding)

#     # Cosine similarity
#     similarity = np.dot(known_vec, uploaded_vec) / (
#         np.linalg.norm(known_vec) * np.linalg.norm(uploaded_vec)
#     )
#     confidence = round(similarity * 100, 2)

#     return similarity >= threshold, confidence


# class FaceVerifyView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         user_id = request.data.get("user_id")
#         image_file = request.FILES.get("image")
#         latitude = request.data.get("latitude")
#         longitude = request.data.get("longitude")

#         if not user_id or not image_file:
#             return Response({"success": False, "error": "user_id and image are required"}, status=400)

#         employee = get_object_or_404(EmployeeDetail, user=user_id)

#         if not employee.profile_pic:
#             return Response({"success": False, "error": "No profile picture found"}, status=404)

#         # Ensure employee has face embedding
#         if not employee.face_encoding:
#             profile_embedding = generate_face_embedding(employee.profile_pic.path)
#             if not profile_embedding:
#                 return Response({"success": False, "error": "No face detected in profile picture"}, status=400)
#             employee.face_encoding = profile_embedding
#             employee.save()

#         # Process uploaded image
#         # Save uploaded file temporarily to generate embedding
#         import tempfile, os
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
#             for chunk in image_file.chunks():
#                 tmp_file.write(chunk)
#             uploaded_path = tmp_file.name

#         uploaded_embedding = generate_face_embedding(uploaded_path)
#         os.remove(uploaded_path)

#         if not uploaded_embedding:
#             return Response({"success": False, "error": "No face detected in uploaded image"}, status=400)

#         # Compare embeddings
#         match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.5)

#         if not match:
#             return Response({
#                 "success": False,
#                 "error": "Face does not match",
#                 "confidence": confidence
#             }, status=401)

#         # If matched, mark attendance
#         user = employee.user
#         refresh = RefreshToken.for_user(user)

#         Attendance.objects.create(
#             employee=employee,
#             date=timezone.now().date(),
#             in_time=timezone.now(),
#             attendance_type="office",
#             status="Present",
#             location=f"{latitude},{longitude}",
#             selfie=image_file,
#             verified_by=user,
#         )

#         return Response({
#             "success": True,
#             "message": "Face matched and check-in recorded",
#             "confidence": confidence,
#             "employee": EmployeeSerializer(employee).data,
#             "user": UserLoginSerializer(user).data,
#             "tokens": {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }
#         })

from .face_utils import generate_face_embedding, compare_faces
import tempfile, os


class FaceVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        image_file = request.FILES.get("image")
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")

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
        match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.7)

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

        late_threshold = time(9, 40)
        if today_punch_count == 0 and in_time_ist.time() > late_threshold:
            status_value = "Late"
            NotificationLog.objects.create(
                user=user,
                action=f"Late punch-in recorded at {in_time_ist.strftime('%H:%M:%S')}",
                title=status_value,
            )
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
            selfie=image_file,
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
    permission_classes = [AllowAny]

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
    def post(self, request):
        user_id = request.data.get("user_id")
        image_file = request.FILES.get("image")
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")

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

        # ------------------------------
        # 3️⃣ Compare embeddings
        # ------------------------------
        match, confidence = compare_faces(employee.face_encoding, uploaded_embedding, threshold=0.7)

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
        attendance.selfie = image_file  # ✅ save logout selfie image
        attendance.location = f"{latitude},{longitude}" if latitude and longitude else attendance.location
        attendance.save()

        # ------------------------------
        # 6️⃣ Return successful response
        # ------------------------------
        return Response({
            "success": True,
            "message": "Face matched and logout recorded successfully.",
            "confidence": confidence,
            "attendance": {
                "date": attendance.date.strftime("%Y-%m-%d"),
                "in_time": attendance.in_time.astimezone().strftime("%H:%M:%S") if attendance.in_time else None,
                "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S"),
                "location": attendance.location,
                "employee": EmployeeSerializer(employee).data
            }
        }, status=200)





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
class QRSessionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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
        code = get_random_string(length=12)

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

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def punch_in_view(request):
    user = request.user

    if user.role != "employee":
        return JsonResponse({"status": "failed", "message": "Only employees can punch-in"}, status=403)

    try:
        employee = user.employee_profile
    except EmployeeDetail.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)

    data = request.data
    qr_code = data.get("qr_code")

    lat_value = data.get("latitude") or data.get("phone_lat")
    lon_value = data.get("longitude") or data.get("phone_lon")
    if lat_value is None or lon_value is None:
        return JsonResponse({"status": "failed", "message": "Latitude and Longitude are required"}, status=400)

    phone_lat = float(lat_value)
    phone_lon = float(lon_value)

    try:
        qrsession = QR_Session.objects.get(code=qr_code)
    except QR_Session.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Invalid QR Code"}, status=400)

    distance = calculate_distance(phone_lat, phone_lon, qrsession.latitudes, qrsession.longitude)
    if distance > 500:  # meters
        return JsonResponse({"status": "failed", "message": "Location mismatch!"}, status=400)

    today = timezone.now().date()

     # ✅ Check if employee has approved leave for today
    approved_leave = Leave.objects.filter(
        employee=employee,
        start_date__lte=today,
        end_date__gte=today,
        status="Approved"
    ).first()

    if approved_leave:
        # ✅ If employee punches in, mark the leave as not taken
        approved_leave.status = "Not Taken"
        approved_leave.save()

        # (Optional) Log or notify
        NotificationLog.objects.create(
            user=user,
            action=f"Leave on {today} marked as 'Not Taken' due to punch-in.",
            title="Leave Updated"
        )

    # Check for active punch-in
    active_punch_in = Attendance.objects.filter(
        employee=employee,
        date=today,
        out_time__isnull=True,
        punch_in=True
    ).first()
    if active_punch_in:
        return JsonResponse({
            "status": "failed",
            "message": "You have an active punch-in session. Please punch-out first."
        }, status=400)

    # Count total punch-ins for today
    today_punch_count = Attendance.objects.filter(employee=employee, date=today).count()

    # Convert punch-in time to IST
    ist = pytz.timezone("Asia/Kolkata")
    in_time_utc = timezone.now()
    in_time_ist = in_time_utc.astimezone(ist)
    
    late_threshold = time(9, 40) 
    # Check for late
    if today_punch_count == 0:
        if in_time_ist.time() > late_threshold:
            status_value = "Late"
            NotificationLog.objects.create(
                user=user,
                action=f"Late punch-in recorded today at {in_time_ist.strftime('%H:%M:%S')}",
                title = "Late"
            )
        else:
            status_value = "Present"
    else:
        # For subsequent punch-ins, don't mark as late or create notification
        status_value = "Present"

    # Create Attendance record
    attendance = Attendance.objects.create(
        employee=employee,
        date=today,
        in_time=in_time_utc,
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
        "employee_id": employee.employee_id,
        "attendance_type": "office",
        "on-site": True,
        "in_time": in_time_ist.strftime("%H:%M:%S"),
        "punch_session": today_punch_count + 1,
        "total_sessions_today": today_punch_count + 1,
        "status_value": status_value
    })

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

        return Response({"success": True, "data": grouped_data})


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
        
        return Response({
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

        

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def punch_out(request):

    user = request.user

    if user.role != "employee":
        return JsonResponse({"status": "failed", "message": "Only employees can punch-out"}, status=403)

    try:
        employee = user.employee_profile
    except EmployeeDetail.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Employee profile not found"}, status=404)

    today = timezone.now().date()

    # Find the most recent active punch-in (punch-in without punch-out)
    attendance = Attendance.objects.filter(
        employee=employee, 
        date=today, 
        out_time__isnull=True,
        punch_in=True
    ).order_by('-in_time').first()
    
    if not attendance:
        return JsonResponse({"status": "failed", "message": "No active punch-in found"}, status=400)

    # Calculate session duration
    session_duration = timezone.now() - attendance.in_time
    duration_hours = session_duration.total_seconds() / 3600

    attendance.out_time = timezone.now()
    attendance.punch_in = False
    attendance.save()

    # Count total completed sessions for today
    completed_sessions = Attendance.objects.filter(
        employee=employee, 
        date=today, 
        out_time__isnull=False
    ).count()

    return JsonResponse({
        "status": "success",
        "message": "Punch-out successful",
        "employee_id": employee.employee_id,
        "out_time": attendance.out_time.astimezone().strftime("%H:%M:%S"),
        "session_duration_hours": round(duration_hours, 2),
        "completed_sessions_today": completed_sessions
    })

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

        return Response({
            "success": True,
            "message": "Monthly counts listed successfully",
            "data": final_data
        })

 # leave applying api
class LeaveApplyingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = LeaveSerializer(data=request.data)

        if serializer.is_valid():
            # Save leave with current user context
            leave = serializer.save(
                user=user,
                employee=getattr(user, "employee_profile", None)
            )

            # Determine who to notify
            if getattr(user, "role", None) in ["admin", "superadmin"]:
                # Admin applies → notify only superadmins
                admins_qs = User.objects.filter(role="superadmin")
            else:
                # Normal employee applies → notify all admins and superadmins
                admins_qs = User.objects.filter(role__in=["admin", "superadmin"])

            # Build action message
            employee_id = getattr(user.employee_profile, "employee_id", None)
            title = "Leave Application"
            action_message = (
                f"Leave request from {user.email}"
                f" ({employee_id})" if employee_id else f"Leave request from {user.email}"
            ) + f" for {leave.start_date} to {leave.end_date}"

            # Create notifications
            for admin_user in admins_qs:
                NotificationLog.objects.create(user=admin_user, action=action_message,title=title)

            return Response({
                "success": True,
                "message": "Leave applied successfully",
                "notified_admins": admins_qs.count()
            })

        return Response({"success": False, "errors": serializer.errors})


# employee leave taken , pending request , balance leave , approved leaves , rejected Leaves , upcoming leaves count api based pn start date and end date 
class DashboardLeaveDetailsCountAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            employee = EmployeeDetail.objects.get(user=user)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee record not found for this user"
            }, status=404)

        start_filter = request.query_params.get("start_date")
        end_filter = request.query_params.get("end_date")

        leaves = Leave.objects.filter(employee=employee)

        if start_filter and end_filter:
            try:
                start_filter = datetime.strptime(start_filter, "%Y-%m-%d").date()
                end_filter = datetime.strptime(end_filter, "%Y-%m-%d").date()
                leaves = leaves.filter(
                    start_date__gte=start_filter,
                    end_date__lte=end_filter
                )
            except ValueError:
                return Response(
                    {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."},
                    status=400
                )

        company_holidays = set(
            Holiday.objects.filter(type="Company Holiday").values_list("date", flat=True)
        )

        def get_working_days(start_date, end_date):
            count = 0
            current = start_date
            while current <= end_date:
                if current.weekday() != 6 and current not in company_holidays:
                    count += 1
                current += timedelta(days=1)
            return count

        def get_total_days_by_status(status_value):
            total_days = 0
            for leave in leaves.filter(status=status_value):
                if leave.start_date and leave.end_date:
                    total_days += get_working_days(leave.start_date, leave.end_date)
            return total_days

        today = date.today()
        total_leave_taken_year = get_total_days_by_status("Approved")
        approved_days = get_total_days_by_status("Approved")
        pending_days = get_total_days_by_status("Pending")
        rejected_days = get_total_days_by_status("Rejected")

        upcoming_days = sum(
            get_working_days(l.start_date, l.end_date)
            for l in leaves.filter(status="Approved", start_date__gt=today)
            if l.start_date and l.end_date
        )

        # ✅ Count of requests (not days)
        approved_count = leaves.filter(status="Approved").count()
        pending_count = leaves.filter(status="Pending").count()
        rejected_count = leaves.filter(status="Rejected").count()
        upcoming_count = leaves.filter(status="Approved", start_date__gt=today).count()

        return Response({
            "success": True,
            "message": "Leave details count fetched successfully",
            "user_id": user.id,
            "employee_id": employee.id,

            # 🧮 Days count (optional)
            "total_leave_taken": total_leave_taken_year,
            # "approved_leave_days": approved_days,
            # "pending_leave_days": pending_days,
            # "rejected_leave_days": rejected_days,
            # "upcoming_leave_days": upcoming_days,

            # 📋 Request count (preferred for dashboard)
            "approved_requests": approved_count,
            "pending_requests": pending_count,
            "rejected_requests": rejected_count,
            "upcoming_requests": upcoming_count,
        })

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
  

# login employees leave list
class LeaveListView(ListAPIView):
    serializer_class = LeaveSerializerview
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Leave.objects.filter(user=self.request.user).order_by('-start_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {
                    "success":False,
                    "message": "No leave records found.",
                    "data": []
                },
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success" : True,
                "message": "Leave records fetched successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

#   login mployees daily tasks api       
class EmployeeTasksWithProjectAPI(ListAPIView):
    serializer_class = TaskWithProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(assigned_to=user).select_related('project').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response(
                {
                    "success": False,
                    "message": "No tasks found for the logged-in employee.",
                    "data": []
                },
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Add summary statistics
        total_tasks = queryset.count()
        pending_tasks = queryset.filter(status="Pending").count()
        in_progress_tasks = queryset.filter(status="In Progress").count()
        completed_tasks = queryset.filter(status="Completed").count()
        
        return Response(
            {
                "success": True,
                "message": "Employee tasks with project details fetched successfully.",
                "data": serializer.data,
                "summary": {
                    "total_tasks": total_tasks,
                    "pending_tasks": pending_tasks,
                    "in_progress_tasks": in_progress_tasks,
                    "completed_tasks": completed_tasks
                }
            },
            status=status.HTTP_200_OK
        )


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
            return Response({
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

        return Response({
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
    

 # get details of first punch in and last punch out details by year , month and day wise of the login employee
class AttendanceReportView(APIView):
    """
    API to get logged-in employee's first punch-in and last punch-out details
    grouped by year, month, and day.
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

        # Fetch all attendances and leaves for the employee
        attendance_qs = Attendance.objects.filter(employee=employee)
        leave_qs = Leave.objects.filter(employee=employee)

        if not attendance_qs.exists() and not leave_qs.exists():
            return Response({
                "success": True,
                "message": "No attendance or leave records found.",
                "data": {}
            }, status=200)

        # Group attendances by date
        grouped_data = defaultdict(list)
        for att in attendance_qs:
            grouped_data[att.date].append(att)

        final_data = defaultdict(lambda: defaultdict(list))

        # Get all unique dates from attendance or leave
        all_dates = set(list(grouped_data.keys()) + list(leave_qs.values_list('requested_date', flat=True)))

        for date in sorted(all_dates):
            day_attendances = grouped_data.get(date, [])

            # First punch-in and last punch-out
            first_in = min([att.in_time for att in day_attendances if att.in_time], default=None)
            last_out = max([att.out_time for att in day_attendances if att.out_time], default=None)

            # Default status
            status = "absent"
            attendance_type = None
            location = None

            if day_attendances:
                # Determine first attendance record (by in_time) to check punctuality
                first_att = min(day_attendances, key=lambda x: x.in_time if x.in_time else timezone.datetime.max)
                attendance_type = first_att.attendance_type
                location = first_att.location

                # If first punch-in exists, convert to local time and compare against threshold
                if first_att.in_time:
                    # Convert to local timezone
                    local_first_in = timezone.localtime(first_att.in_time)
                    threshold = time(9, 40)
                    if local_first_in.time() <= threshold:
                        status = "present"
                    else:
                        status = "late"
                else:
                    # No in_time in records → mark absent
                    status = "absent"

            # Check leave for this date
            leave = leave_qs.filter(
                start_date__lte=date,
                end_date__gte=date
            ).first()

            if leave:
                leave_status = leave.status.lower()
                if leave_status == "approved":
                    status = "leave"
                elif leave_status == "rejected":
                    status = "absent"
                elif leave_status == "not taken":
                    # ✅ Treat as working day — check punch-in time
                    if first_in:
                        local_first_in = timezone.localtime(first_in)
                        threshold = time(9, 40)
                        if local_first_in.time() <= threshold:
                            status = "present"
                        else:
                            status = "late"
                    else:
                        status = "absent"  # If no attendance record at all

            year = date.year
            month = date.month

            daily_summary = {
                "date": date.strftime("%Y-%m-%d"),
                "first_punch_in": first_in.astimezone().strftime("%H:%M:%S") if first_in else None,
                "last_punch_out": last_out.astimezone().strftime("%H:%M:%S") if last_out else None,
                "status": status,
                "attendance_type": attendance_type,
                "location": location
            }

            final_data[str(year)][str(month)].append(daily_summary)

        return Response({
            "success": True,
            "message": "First punch-in and last punch-out details with status retrieved successfully.",
            "data": final_data
        }, status=200)
    

  # employee notifications api
class NotificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = NotificationLog.objects.filter(user=user,is_active=True).order_by('-timestamp')
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            "success": True,
            "message": "Notifications fetched successfully",
            "data": serializer.data
        }) 
    

 # delete employee notification api
class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        user = request.user
        try:
            notification = NotificationLog.objects.get(id=notification_id, user=user)
            # Soft-delete: mark notification as inactive instead of removing it
            notification.is_active = False
            notification.save()
            return Response({
                "success": True,
                "message": "Notification deleted successfully"
            })
        except NotificationLog.DoesNotExist:
            return Response({
                "success": False,
                "message": "Notification not found"
            }, status=404)   


# notification undo api
class UndoNotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        user = request.user
        try:
            notification = NotificationLog.objects.get(id=notification_id, user=user)
            # Undo soft-delete: mark notification as active again
            notification.is_active = True
            notification.save()
            return Response({
                "success": True,
                "message": "Notification restored successfully"
            })
        except NotificationLog.DoesNotExist:
            return Response({
                "success": False,
                "message": "Notification not found"
            }, status=404)




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

        # -------------------
        # 2. Fetch Public Holidays (full-year count + month-filtered display list)
        # -------------------
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

        # -------------------
        # 3. Combine Company + Public Holidays
        # -------------------
        all_holidays = company_data + public_holiday_list

        # -------------------
        # 4. Group Month-Wise
        # -------------------
        month_wise = defaultdict(list)
        for h in all_holidays:
            # Parse date if it's string (from serializer)
            if isinstance(h['date'], str):
                dt = datetime.strptime(h['date'], "%Y-%m-%d")
            else:
                dt = h['date']  # already a date object

            month_key = dt.month
            month_wise[month_key].append(h)

        # Convert defaultdict to normal dict for JSON response
        month_wise = dict(month_wise)

        # Single total holiday count for the year (company + public)
        total_holidays = company_count + public_count

        return Response({
            "success": True,
            "message": "Holiday list fetched successfully",
            "total_holidays": total_holidays,
            "data": month_wise
        }, status=status.HTTP_200_OK)
    


# # push notification function want to implement later
# def send_push_notification(user, title, message):
#     try:
#         device = FCMDevice.objects.get(user=user)
#         device.send_message(title=title, body=message)
#     except FCMDevice.DoesNotExist:
#         pass  # No device found for user, skip sending notification        

# logout api to blacklist the refresh token
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # ← this adds it to blacklist
            return Response(
                {"success": True, "message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {"success": False, "message": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )