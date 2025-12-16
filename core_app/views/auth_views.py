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
import os
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
from core_app.utils.transit_encryption import rsa_decrypt_key, aes_decrypt
import json
from core_app.utils.encrypt_decrypt_data import *
from core_app.utils.transit_encryption import *
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from core_app.utils.react_crypto import *
from django.core.cache import cache
# -----------------------------
# Utility
# -----------------------------
def generate_otp():
    return str(random.randint(1000, 9999))


# -----------------------------
# Login View
# -----------------------------
# api health check view
def health_check(request):
    return JsonResponse({"status": "OK", "message": "API is healthy"})


def get_user_by_encrypted_email(email):
    for u in User.objects.all():
        try:
            decrypted_email = decrypt_value(u.email)
            if decrypted_email.lower() == email.lower():
                return u
        except Exception:
            continue
    return None



class TestEnc(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        response =  Response({"status": "ok"})
        response.encrypt_payload = True       
        return response


# login api
# class LoginView(APIView):
#     renderer_classes = [JSONRenderer]
#     permission_classes = [AllowAny]


#     def post(self, request):
#         email = request.data.get("email")
#         password = request.data.get("password")

#         if not email or not password:
#             return Response(
#                 {"success": False, "message": "Email and password are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # try:
#         #     user = User.objects.get(email=email)  # ✅ custom User
#         # except User.DoesNotExist:
#         #     return Response(
#         #         {"success": False, "message": "Invalid email or password"},
#         #         status=status.HTTP_401_UNAUTHORIZED
#         #     )

#         # 🔒 Decrypt and match manually
#         user = None
#         for u in User.objects.all():
#             try:
#                 decrypted_email = decrypt_value(u.email)
#                 if decrypted_email.lower() == email.lower():
#                     user = u
#                     break
#             except Exception:
#                 continue

#         if not check_password(password, user.password):
#             return Response(
#                 {"success": False, "message": "Invalid email or password"},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )
        
#         if not user.is_active:
#             return Response(
#                 {"success": False, "message": "Account is inactive. Contact admin."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # ----------------------------
#         # Role → Privileges mapping
#         # ----------------------------
#         if user.role == "superadmin":
#             privileges = ["superadmin"]
#         elif user.role == "admin":
#             privileges = ["admin", "employee"]  # ✅ team lead = both
#         else:
#             privileges = ["employee"]

#         # ----------------------------
#         # Employee Info (safe access)
#         # ----------------------------
#         employee_id = None
#         company_branch_id = None

#         if hasattr(user, "employee_profile"):
#             employee_profile = user.employee_profile
#             employee_id = getattr(employee_profile, "id", None)
#             # ✅ Safe handling for company_branch (ForeignKey can be null)
#             company_branch_id = (
#                 employee_profile.company_branch.id
#                 if employee_profile.company_branch
#                 else None
#             )
#         refresh = RefreshToken.for_user(user)
#         refresh["role"] = user.role  # include role in token
#         refresh["user_id"] = user.id 
#         refresh["employee_id"] = employee_id
#         refresh["company_branch_id"] = company_branch_id    


        

#         return Response(
#             {
#                 "success": True,
#                 "message": "Login successful",
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "role": user.role,
#                     "employee_id": employee_id,
#                     "company_branch_id": company_branch_id,
#                     "privileges": privileges,
                    
#                 },

#                 "access": str(refresh.access_token),
#                 "refresh": str(refresh),
#             },
#             status=status.HTTP_200_OK
#         )
# class LoginView(APIView):
#     renderer_classes = [JSONRenderer]
#     permission_classes = [AllowAny]

#     def post(self, request):
#         print("Login Request Data:", request.data)

#         encrypted_key = request.data.get("encrypted_key")
#         cipher = request.data.get("cipher")
#         nonce = request.data.get("nonce")
#         tag = request.data.get("tag")

#         # ------------------------------------------
#         # Case 1: Encrypted Login Payload (App/React)
#         # ------------------------------------------
#         if encrypted_key and cipher and nonce and tag:
#             try:
#                 aes_key = rsa_decrypt_key(encrypted_key)
#                 decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
#                 login_data = json.loads(decrypted_json)

#                 email = login_data.get("email")
#                 password = login_data.get("password")

#             except Exception as e:
#                 print("Decryption Error:", str(e))
#                 return Response(
#                     {"success": False, "message": "Invalid encrypted payload"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#         # ------------------------------------------
#         # Case 2: Normal Login (Postman / Debugging)
#         # ------------------------------------------
#         else:
#             email = request.data.get("email")
#             password = request.data.get("password")

#         if not email or not password:
#             return Response(
#                 {"success": False, "message": "Email and password required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # ------------------------------------------
#         # Validate Credentials
#         # ------------------------------------------
#         user = None
#         for u in User.objects.all():
#             try:
#                 decrypted_email = decrypt_value(u.email)
#                 if decrypted_email.lower() == email.lower():
#                     user = u
#                     break
#             except:
#                 continue

#         if not user or not check_password(password, user.password):
#             return Response(
#                 {"success": False, "message": "Invalid email or password"},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )

#         if not user.is_active:
#             return Response(
#                 {"success": False, "message": "Account inactive"},
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         # Employee details
#         employee_id = getattr(user.employee_profile, "id", None)
#         company_branch_id = (
#             getattr(user.employee_profile.company_branch, "id", None)
#             if employee_id
#             else None
#         )

#         # Create JWT
#         refresh = RefreshToken.for_user(user)
#         refresh["role"] = user.role
#         refresh["user_id"] = user.id
#         refresh["employee_id"] = employee_id
#         refresh["company_branch_id"] = company_branch_id

#         response_payload = {
#             "success": True,
#             "message": "Login successful",
#             "user": {
#                 "id": user.id,
#                 "email": email,
#                 "role": user.role,
#                 "employee_id": employee_id,
#                 "company_branch_id": company_branch_id,
#             },
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#         }

#         # ---------------------------------------------------------
#         # Encrypt response with the stored AES session key
#         # ---------------------------------------------------------
#         aes_key_b64 = request.session.get("aes_session_key")
#         if not aes_key_b64:
#             return Response(
#                 {"error": "AES session key missing. Register before calling login."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         aes_key = base64.b64decode(aes_key_b64)

#         json_data = json.dumps(response_payload, separators=(",", ":"))
#         aes = AES.new(aes_key, AES.MODE_GCM)
#         cipher_bytes, tag = aes.encrypt_and_digest(json_data.encode())

#         return Response(
#             {
#                 "cipher": base64.b64encode(cipher_bytes).decode(),
#                 "nonce": base64.b64encode(aes.nonce).decode(),
#                 "tag": base64.b64encode(tag).decode(),
#             },
#             status=status.HTTP_200_OK,
#         )
# class LoginView(APIView):
#     renderer_classes = [JSONRenderer]
#     permission_classes = [AllowAny]

#     def post(self, request):
#         print("Login Request Data:", request.data)  # Debugging line

#         encrypted_key = request.data.get("encrypted_key")
#         cipher = request.data.get("cipher")
#         nonce = request.data.get("nonce")
#         tag = request.data.get("tag")

#         # ------------------------------------------------------------------
#         # CASE 1: IF RSA + AES ENCRYPTED PAYLOAD IS PROVIDED
#         # ------------------------------------------------------------------
#         if encrypted_key and cipher and nonce and tag:
#             try:
#                 aes_key = rsa_decrypt_key(encrypted_key)
#                 decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
#                 login_data = json.loads(decrypted_json)

#                 email = login_data.get("email")
#                 password = login_data.get("password")

#             except Exception as e:
#                 return Response(
#                     {"success": False, "message": "Invalid encrypted payload"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # ------------------------------------------------------------------
#         # CASE 2: NORMAL LOGIN (NO ENCRYPTION FROM FLUTTER)
#         # ------------------------------------------------------------------
#         else:
#             email = request.data.get("email")
#             password = request.data.get("password")

#             # Validate
#             if not email or not password:
#                 return Response(
#                     {"success": False, "message": "email and password required."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # ---------------------------------------------------------------
#         # Find user by decrypting stored encrypted emails
#         # ---------------------------------------------------------------
#         user = None
#         for u in User.objects.all():
#             try:
#                 decrypted_email = decrypt_value(u.email)
#                 if decrypted_email.lower() == email.lower():
#                     user = u
#                     break
#             except Exception:
#                 continue

#         if not user or not check_password(password, user.password):
#             return Response(
#                 {"success": False, "message": "Invalid email or password"},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )

#         if not user.is_active:
#             return Response(
#                 {
#                     "success": False,
#                     "message": "Account is inactive. Contact admin."
#                 },
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # ----------------------------
#         # Role → Privileges mapping
#         # ----------------------------
#         if user.role == "superadmin":
#             privileges = ["superadmin"]
#         elif user.role == "admin":
#             privileges = ["admin", "employee"]  # Team lead = admin + employee
#         else:
#             privileges = ["employee"]

#         # ----------------------------
#         # Employee Info (safe access)
#         # ----------------------------
#         employee_id = None
#         company_branch_id = None

#         if hasattr(user, "employee_profile"):
#             employee_profile = user.employee_profile
#             employee_id = getattr(employee_profile, "id", None)
#             company_branch_id = (
#                 employee_profile.company_branch.id
#                 if employee_profile.company_branch
#                 else None
#             )

#         # ----------------------------
#         # JWT Token with extra claims
#         # ----------------------------
#         refresh = RefreshToken.for_user(user)
#         refresh["role"] = user.role
#         refresh["user_id"] = user.id
#         refresh["employee_id"] = employee_id
#         refresh["company_branch_id"] = company_branch_id

#         # ----------------------------
#         # Response
#         # ----------------------------
#         return Response(
#             {
#                 "success": True,
#                 "message": "Login successful",
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "role": user.role,
#                     "employee_id": employee_id,
#                     "company_branch_id": company_branch_id,
#                     "privileges": privileges,
#                 },
#                 "access": str(refresh.access_token),
#                 "refresh": str(refresh),
#             },
#             status=status.HTTP_200_OK
#         )


# -----------------------------
# Register Session Key
# Register Session Key
class RegisterSessionKey(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        print("\n====== /register-session-key/ CALLED ======")
        print("Incoming RAW request data:", request.data)
        print("Incoming session ID:", request.session.session_key)

        encrypted_key = request.data.get("encrypted_key")
        if not encrypted_key:
            print("ERROR: encrypted_key missing in request")
            return Response({"error": "encrypted_key missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print("Encrypted AES key (base64) received:", encrypted_key)

            # Step 1: RSA decrypt
            aes_key = rsa_decrypt_key(encrypted_key)

            print("AES key decrypted (bytes):", aes_key)
            print("AES key length:", len(aes_key))

            # Step 2: Store AES key base64 in session
            encoded_key = base64.b64encode(aes_key).decode("ascii")
            request.session["aes_session_key"] = encoded_key

            # Force Django to store session
            request.session.modified = True
            request.session.save()

            print("AES key saved in session as base64:", encoded_key)
            print("Session stored successfully!")
            print("New session ID after save:", request.session.session_key)
            print("Session data now:", dict(request.session))

            return Response({"message": "AES key registered"}, status=status.HTTP_200_OK)

        except Exception as e:
            print("ERROR while registering AES key:", str(e))
            return Response({"error": f"Failed to register AES key: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# Login view (handles three cases)
class LoginView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

    def post(self, request):

        should_encrypt_response = False  

        print("\n==================== LOGIN API CALLED ====================")
        print("RAW request.data:", request.data)
        print("Incoming COOKIES:", request.COOKIES)
        print("Session Key:", request.session.session_key)
        print("Session BEFORE:", dict(request.session))

        email = None
        password = None

        # Shared encrypted fields
        encrypted_key = request.data.get("encrypted_key")
        cipher = request.data.get("cipher")
        nonce = request.data.get("nonce")
        tag = request.data.get("tag")

        # ============================================================
        # CASE A: FLUTTER (RSA + AES)
        # ============================================================
        if encrypted_key and cipher and nonce and tag:
            should_encrypt_response = True     # <---- ENABLE ENCRYPTION

            print("CASE A: Flutter AES + RSA detected")

            try:
                aes_key = rsa_decrypt_key(encrypted_key)
                decrypted_json = aes_gcm_decrypt(cipher, nonce, tag, aes_key)

                email = decrypted_json.get("email")
                password = decrypted_json.get("password")

            except Exception as e:
                print("Flutter Decryption FAILED:", e)

                response = Response({
                    "success": False,
                    "message": "Invalid Flutter encrypted payload"
                }, status=status.HTTP_400_BAD_REQUEST)

                response.encrypt_payload = True
                return response

        else:
            # ============================================================
            # CASE B: REACT AES_SESSION_KEY stored in session
            # ============================================================
            if cipher and nonce and tag:
                should_encrypt_response = True     # <---- ENABLE ENCRYPTION

                print("CASE B: React WebCrypto AES-GCM detected")
                b64_aes = request.session.get("aes_session_key")

                if not b64_aes:
                    print(" No AES session key in session")

                    response = Response({
                        "success": False,
                        "message": "AES session key missing. Register session first."
                    }, status=status.HTTP_400_BAD_REQUEST)

                    response.encrypt_payload = True
                    return response

                try:
                    aes_key_bytes = base64.b64decode(b64_aes)
                    decrypted = aes_gcm_decrypt(cipher, nonce, tag, aes_key_bytes)

                    email = decrypted.get("email")
                    password = decrypted.get("password")

                except Exception as e:
                    print("React AES Decryption FAILED:", e)

                    response = Response({
                        "success": False,
                        "message": "Invalid React encrypted payload"
                    }, status=status.HTTP_400_BAD_REQUEST)

                    response.encrypt_payload = True
                    return response

            else:
                # ============================================================
                # CASE C: PLAIN JSON LOGIN
                # ============================================================
                print("CASE C: Plain JSON Login")
                email = request.data.get("email")
                password = request.data.get("password")

        # ------------------------------------------------------------
        # Missing Credentials
        # ------------------------------------------------------------
        if not email or not password:

            response = Response({
                "success": False,
                "message": "email and password required"
            }, status=status.HTTP_400_BAD_REQUEST)

            if should_encrypt_response:
                response.encrypt_payload = True
            
            return response

        # ------------------------------------------------------------
        # AUTHENTICATION LOGIC
        # ------------------------------------------------------------
        user = None
        for u in User.objects.all():
            try:
                decrypted_email = decrypt_value(u.email)
                if decrypted_email.lower() == email.lower():
                    user = u
                    break
            except:
                continue

        if not user:
            response = Response({
                "success": False,
                "message": "Invalid email or password"
            }, status=status.HTTP_401_UNAUTHORIZED)

            if should_encrypt_response:
                response.encrypt_payload = True

            return response

        if not check_password(password, user.password):
            response = Response({
                "success": False,
                "message": "Invalid email or password"
            }, status=status.HTTP_401_UNAUTHORIZED)

            if should_encrypt_response:
                response.encrypt_payload = True

            return response

        if not user.is_active:
            response = Response({
                "success": False,
                "message": "Account inactive. Contact admin."
            }, status=status.HTTP_403_FORBIDDEN)

            if should_encrypt_response:
                response.encrypt_payload = True

            return response

        # ------------------------------------------------------------
        # SUCCESSFUL LOGIN
        # ------------------------------------------------------------
        employee_id = getattr(user.employee_profile, "id", None) \
            if hasattr(user, "employee_profile") else None

        company_branch_id = getattr(
            user.employee_profile.company_branch, "id", None
        ) if hasattr(user, "employee_profile") else None

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["user_id"] = user.id
        refresh["employee_id"] = employee_id
        refresh["company_branch_id"] = company_branch_id

        response = Response({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "employee_id": employee_id,
                "company_branch_id": company_branch_id,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

        # Encrypt ONLY if request was encrypted
        if should_encrypt_response:
            response.encrypt_payload = True

        return response


# class LoginView(APIView):
#     renderer_classes = [JSONRenderer]
#     permission_classes = [AllowAny]

#     def post(self, request):
#         print("Login Request Raw Data:", request.data)

#         email = None
#         password = None

#         # ================================================================
#         # CASE 1: FLUTTER → RSA(OAEP) + AES(GCM)
#         # ================================================================
#         encrypted_key = request.data.get("encrypted_key")
#         cipher = request.data.get("cipher")
#         nonce = request.data.get("nonce")
#         tag = request.data.get("tag")

#         if encrypted_key and cipher and nonce and tag:
#             print("Decrypting Flutter Payload...")
#             try:
#                 aes_key = rsa_decrypt_key(encrypted_key)
#                 decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
#                 data = json.loads(decrypted_json)

#                 email = data.get("email")
#                 password = data.get("password")
#             except Exception as e:
#                 print("Flutter Decryption FAILED:", str(e))
#                 return Response(
#                     {"success": False, "message": "Invalid Flutter encrypted payload"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         else:
#             # ================================================================
#             # CASE 2: REACT → AES-GCM WebCrypto (cipher includes tag)
#             # ================================================================
#             cipher = request.data.get("cipher")
#             nonce = request.data.get("nonce")

#             if cipher and nonce:
#                 print("Decrypting React AES-GCM Payload...")
#                 try:
#                     data = aes_gcm_decrypt(cipher, nonce)
#                     email = data.get("email")
#                     password = data.get("password")

#                 except Exception as e:
#                     print("React Decryption FAILED:", str(e))
#                     return Response(
#                         {"success": False, "message": "Invalid React encrypted payload"},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#             else:
#                 # ================================================================
#                 # CASE 3: NORMAL JSON (Postman, Browser, etc.)
#                 # ================================================================
#                 print("Processing normal login payload...")
#                 email = request.data.get("email")
#                 password = request.data.get("password")

    
#         if not email or not password:
#             return Response(
#                 {"success": False, "message": "email and password required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Search user by decrypting stored encrypted emails
#         user = None
#         for u in User.objects.all():
#             try:
#                 if decrypt_value(u.email).lower() == email.lower():
#                     user = u
#                     break
#             except Exception:
#                 continue

#         if not user or not check_password(password, user.password):
#             return Response(
#                 {"success": False, "message": "Invalid email or password"},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )

#         if not user.is_active:
#             return Response(
#                 {"success": False, "message": "Account inactive. Contact admin."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Role privileges
#         privileges = (
#             ["superadmin"] if user.role == "superadmin" else
#             ["admin", "employee"] if user.role == "admin" else
#             ["employee"]
#         )

#         employee_id = getattr(user.employee_profile, "id", None) if hasattr(user, "employee_profile") else None
#         company_branch_id = getattr(user.employee_profile.company_branch, "id", None) if hasattr(user, "employee_profile") else None

#         # JWT
#         refresh = RefreshToken.for_user(user)
#         refresh["role"] = user.role
#         refresh["user_id"] = user.id
#         refresh["employee_id"] = employee_id
#         refresh["company_branch_id"] = company_branch_id

#         response_data = {
#             "success": True,
#             "message": "Login successful",
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "role": user.role,
#                 "employee_id": employee_id,
#                 "company_branch_id": company_branch_id,
#                 "privileges": privileges,
#             },
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#         }

#         return Response(response_data, status=status.HTTP_200_OK)


# check whether the user in logged in or not 
class CheckLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.data) 
    
        user = request.user
        response =  Response({
            "success": True,
            "message": "User is already logged in",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        })
        response.encrypt_payload = True     
        return response


# -----------------------------
# refreshing token api 
# class RefreshTokenView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         print("Leave Application Request Data:", request.data) 
#         decrypted_data = decrypt_request_payload(request)

#         if decrypted_data:
#             print("Decrypted Leave Request:", decrypted_data)
#             # Replace request.data with decrypted version
#             data = decrypted_data
#         else:
#             print("Normal Leave Request:", request.data)
#             data = request.data
#         refresh_token = data.get("refresh")

#         if not refresh_token:
#             response =  Response(
#                 {"success": False, "message": "Refresh token is required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#             response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
#             return response

#         try:
#             # Verify & decode refresh token
#             old_refresh = RefreshToken(refresh_token)
#             user_id = old_refresh.get("user_id")

#             # Fetch user
#             try:
#                 user = User.objects.get(id=user_id)
#             except User.DoesNotExist:
#                 response = Response(
#                     {"success": False, "message": "User not found"},
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )
#                 response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
#                 return response
            
#             if not user.is_active:
#                 response = Response(
#                     {
#                         "success": False,
#                         "message": "User account is inactive. Token refresh not allowed.",
#                     },
#                     status=status.HTTP_403_FORBIDDEN,
#                 )
#                 response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
#                 return response

#             # Issue new refresh + access
#             new_refresh = RefreshToken.for_user(user)
#             new_refresh["role"] = user.role
#             new_refresh["user_id"] = user.id

#             response = Response(
#                 {
#                     "success": True,
#                     "message": "Token refreshed successfully",
#                     "access": str(new_refresh.access_token),
#                     "refresh": str(new_refresh),
#                     "user": {
#                         "id": user.id,
#                         "email": user.email,
#                         "role": user.role,
#                     },
#                 },
#                 status=status.HTTP_200_OK,

#             )
#             response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
#             return response

#         except TokenError:
#             response =  Response(
#                 {"success": False, "message": "Invalid or expired refresh token"},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )
#         response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
#         return response
# -----------------------------
# Refresh Token API
# -----------------------------
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        should_encrypt_response = False   # <--- IMPORTANT

        print("\n==================== REFRESH TOKEN API ====================")
        print("RAW request.data:", request.data)

        # Try decryption (Flutter or React AES)
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Refresh Token Request:", decrypted_data)

            data = decrypted_data
            should_encrypt_response = True      # <---- encrypted request → encrypted response

        else:
            print("Normal Refresh Token Request:", request.data)
            data = request.data                 # normal request, keep plain JSON


        refresh_token = data.get("refresh")

        if not refresh_token:
            response = Response(
                {"success": False, "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

            if should_encrypt_response:
                response.encrypt_payload = True

            return response

        try:
            # Decode refresh token
            old_refresh = RefreshToken(refresh_token)
            user_id = old_refresh.get("user_id")

            # Get user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:

                response = Response(
                    {"success": False, "message": "User not found"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

                if should_encrypt_response:
                    response.encrypt_payload = True

                return response
            
            if not user.is_active:
                response = Response(
                    {
                        "success": False,
                        "message": "User account is inactive. Token refresh not allowed.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

                if should_encrypt_response:
                    response.encrypt_payload = True

                return response

            # Create new tokens
            new_refresh = RefreshToken.for_user(user)
            new_refresh["role"] = user.role
            new_refresh["user_id"] = user.id

            response = Response(
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

            if should_encrypt_response:
                response.encrypt_payload = True

            return response

        except TokenError:

            response = Response(
                {"success": False, "message": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

            if should_encrypt_response:
                response.encrypt_payload = True

            return response


# -----------------------------
# Forgot Password (OTP)
# -----------------------------


# Utility to generate OTP and hash
def generate_otp():
    otp = str(random.randint(1000, 9999)) 
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    return otp, otp_hash
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        decrypted_data = decrypt_request_payload(request)
        data = decrypted_data if decrypted_data else request.data

        email = data.get("email")
        if not email:
            return Response({"success": False, "error": "Email is required"}, status=400)

        try:
            user = get_user_by_encrypted_email(email=email)
        except User.DoesNotExist:
            user = None

        if user is None:
            response = Response({"success": False, "error": "Email not registered"}, status=404)
            response.encrypt_payload = True
            return response

        # otp, otp_hash = generate_otp()
        # expiry = timezone.now() + timezone.timedelta(minutes=2)
        EmailOTP.objects.filter(
            user=user,
            purpose__in=["reset_password", "resend-otp"],
            is_used=False,
        ).update(is_used=True, expires_at=timezone.now())

        otp, otp_hash = generate_otp()
        expiry = timezone.now() + timezone.timedelta(seconds=60)

        
        EmailOTP.objects.create(user=user, otp_hash=otp_hash, purpose="reset_password", expires_at=expiry)

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP for password reset is: {otp}",
            from_email="no-reply@example.com",
            recipient_list=[email],
            fail_silently=False,
        )

        response = Response({"success": True, "message": "OTP sent to your email"}, status=200)
        response.encrypt_payload = True
        return response



# resend otp view
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Leave Request:", decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data

        email = data.get("email")
        if not email:
            return Response({"success": False, "error": "Email is required"}, status=400)

        try:
            user = get_user_by_encrypted_email(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "error": "Email not found"}, status=404)

        otp, otp_hash = generate_otp()
        expiry = timezone.now() + timezone.timedelta(seconds=60)

        EmailOTP.objects.create(user=user, otp_hash=otp_hash, purpose="resend-otp", expires_at=expiry)

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP for password reset is: {otp}",
            from_email="no-reply@example.com",
            recipient_list=[email],
            fail_silently=False,
        )

        response =  Response({"success": True, "message": "OTP re-sent to your email"}, status=200)
        response.encrypt_payload = True     
        return response


# -----------------------------
# Verify OTP
# -----------------------------

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Leave Request:", decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data

        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            response = Response({"success": False, "error": "Email and OTP are required"}, status=400)
            response.encrypt_payload = True    
            return response

        try:
            user = get_user_by_encrypted_email(email=email)
        except User.DoesNotExist:
            response = Response({"success": False, "error": "Invalid email"}, status=404)
            response.encrypt_payload = True     
            return response

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        otp_record = EmailOTP.objects.filter(
            user=user,
            otp_hash=otp_hash,
            is_used=False,
            purpose__in=["reset_password", "resend-otp"],
            expires_at__gte=timezone.now()
        ).last()

        if not otp_record:
            response= Response({"success": False, "error": "OTP invalid or expired"}, status=400)
            response.encrypt_payload = True       
            return response

        otp_record.is_used = True
        otp_record.is_verified = True  
        otp_record.save()

        response  =  Response({"success": True, "message": "OTP verified successfully"}, status=200)
        response.encrypt_payload = True      
        return response
# -----------------------------
# Reset Password
# -----------------------------
from django.contrib.auth.hashers import make_password

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print("Decrypted Leave Request:", decrypted_data)
            # Replace request.data with decrypted version
            data = decrypted_data
        else:
            print("Normal Leave Request:", request.data)
            data = request.data
        email = data.get("email")
        new_password = data.get("new_password")

        if not email or not new_password:
            return Response({"success": False, "error": "Email and new password are required"}, status=400)

        try:
            user = get_user_by_encrypted_email(email=email)
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
                    "isOnline": True  
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
        response =  Response({
            "success": True,
            "employee": serializer.data
        }, status=200)
        response.encrypt_payload = True       
        return response

# -----------------------------
# Notification
# -----------------------------
# class NotificationStatusView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         unread = NotificationLog.objects.filter(user=request.user).count()
#         return Response({'unreadCount': unread})


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
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print(decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print(request.data)
        #         data = request.data
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
                privileges = ["admin", "employee"]  
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
                        "repMgrTl": employee.reporting_manager,  
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

      
        return Response(
            {"success": False, 
             "errors": serializer.errors
             },
            status=status.HTTP_400_BAD_REQUEST
        )

# -----------------------------
# Register Session Key
# class RegisterSessionKey(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         encrypted_key = request.data.get("encrypted_key")
#         if not encrypted_key:
#             return Response({"error": "encrypted_key missing"}, status=400)

#         try:
#             aes_key = rsa_decrypt_key(encrypted_key)

#             # Save AES key in session
#             request.session["aes_session_key"] = base64.b64encode(aes_key).decode()
#             request.session.save()  # 🔥 VERY IMPORTANT

#             return Response({"message": "AES key registered"})
#         except Exception as e:
#             return Response({"error": str(e)}, status=400)

        

# class RegisterSessionKey(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         encrypted_key = request.data.get("encrypted_key")
#         client_id = request.data.get("client_id")   # <-- Required

#         if not encrypted_key or not client_id:
#             return Response({"error": "encrypted_key and client_id required"}, status=400)

#         try:
#             # 1. Decrypt AES key using RSA
#             aes_key = rsa_decrypt_key(encrypted_key)

#             # 2. Store AES key in CACHE
#             cache_key = f"aes_key:{client_id}"
#             cache.set(cache_key, aes_key, timeout=3600)  # 1 hour

#             return Response({"message": "AES key registered successfully"})

#         except Exception as e:
#             return Response({"error": f"Key registration failed: {str(e)}"}, status=400)        


#logout api to blacklist the refresh token

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data) 
        decrypted_data = decrypt_request_payload(request)

        if decrypted_data:
            print(decrypted_data)
          
            data = decrypted_data
        else:
            print(request.data)
            data = request.data
        refresh_token = data.get("refresh")

        if not refresh_token:
            response =  Response(
                {"success": False, "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            response.encrypt_payload = True      
            return response

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  
            response  =  Response(
                {"success": True, "message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )
            response.encrypt_payload = True    
            return response
        except TokenError:
            response =  Response(
                {"success": False, "message": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
            response.encrypt_payload = True     
            return response
        

        