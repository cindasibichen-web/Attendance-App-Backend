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
from core_app.utils.react_crypto import decrypt_react_payload, aes_gcm_encrypt




# proile details of login admin
# Admin profile view        
class AdminProfileView(RetrieveAPIView):
    serializer_class = AdminProfileSerializerView
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Check role
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can access this profile.",
                    "data": {}
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Get employee profile (related to User)
        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Employee profile not found for this admin.",
                    "data": {}
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(employee)
        return Response(
            {
                "success": True,
                "message": "Admin profile fetched successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

# edit admin profile api
class AdminEditProfile(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        print(request.data) 
        decrypted_data = decrypt_react_payload(request)

        if decrypted_data:
                print("Decrypted Request:", decrypted_data)
                # Replace request.data with decrypted version
                data = decrypted_data
        else:
                print("Normal  Request:", request.data)
                data = request.data
        user = request.user

        # Allow only admin/superadmin
        if user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can edit this profile.",
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            employee = user.employee_profile
        except EmployeeDetail.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Employee profile not found.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminProfileSerializerView(employee, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Profile edited successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "message": "Profile update failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# login users notification list 

class AdminNotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Allow only admin/superadmin
        if user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can access notifications.",
                    "data": []
                },
                status=status.HTTP_403_FORBIDDEN
            )

        notifications = NotificationLog.objects.filter(user=user, is_active=True)
        serializer = NotificationLogSerializer(notifications, many=True)

        return Response({
            "success": True,
            "message": "Notifications fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# admin notification delete api
class AdminNotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        user = request.user
        # Allow only admin/superadmin
        if user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can delete notifications."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            notification = NotificationLog.objects.get(id=notification_id, user=user)
   
            notification.is_active = False
            notification.save()
            return Response(
                {
                    "success": True,
                    "message": "Notification deleted successfully."
                },
                status=status.HTTP_200_OK
            )
        except NotificationLog.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Notification not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
# get email of login users 
class AdminEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Allow only admin/superadmin
        if user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can access email.",
                    "data": {}
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "success": True,
                "message": "Email fetched successfully.",
                "data": {"email": user.email}
            },
            status=status.HTTP_200_OK
        )        