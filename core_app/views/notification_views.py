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


  # employee notifications api
class NotificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        user = request.user
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        # All notifications (latest first)
        notifications = NotificationLog.objects.filter(user=user,is_active=True).order_by('-timestamp')

        # Group by date
        today_qs = notifications.filter(timestamp__date=today)
        yesterday_qs = notifications.filter(timestamp__date=yesterday)
        older_qs = notifications.exclude(timestamp__date__in=[today, yesterday])

        # Serialize each group
        today_data = NotificationSerializer(today_qs, many=True).data
        yesterday_data = NotificationSerializer(yesterday_qs, many=True).data

        # Group older by date (each day as heading)
        older_grouped = {}
        for notif in older_qs:
            date_str = notif.timestamp.date().strftime("%Y-%m-%d")
            if date_str not in older_grouped:
                older_grouped[date_str] = []
            older_grouped[date_str].append(NotificationSerializer(notif).data)

        # Sort older dates descending
        older_sorted = dict(sorted(older_grouped.items(), reverse=True))

        # Always include all sections, even if empty
        data = {
            "Today": today_data if today_data else [],
            "Yesterday": yesterday_data if yesterday_data else [],
            "Older": older_sorted if older_sorted else {}
        }

        response =  Response({
            "success": True,
            "message": "Notifications fetched successfully",
            "data": data
        })
        response.encrypt_payload = True   
        return response
    

 # delete employee notification api
class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        print("Raw:", request.data)
        decrypted_data = decrypt_request_payload(request)

        data = decrypted_data if decrypted_data else request.data
        print("Final Data Used:", data)

        user = request.user
        try:
            notification = NotificationLog.objects.get(id=notification_id, user=user)
            # Soft-delete: mark notification as inactive instead of removing it
            notification.is_active = False
            notification.save()
            response =  Response({
                "success": True,
                "message": "Notification deleted successfully"
            })
            response.encrypt_payload = True     
            return response
        except NotificationLog.DoesNotExist:
            response =  Response({
                "success": False,
                "message": "Notification not found"
            }, status=404)   
            response.encrypt_payload = True     
            return response


# notification undo api
class UndoNotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        print("Raw:", request.data)
        decrypted_data = decrypt_request_payload(request)

        data = decrypted_data if decrypted_data else request.data
        print("Final Data Used:", data)

        user = request.user
        try:
            notification = NotificationLog.objects.get(id=notification_id, user=user)
            # Undo soft-delete: mark notification as active again
            notification.is_active = True
            notification.save()
            response =  Response({
                "success": True,
                "message": "Notification restored successfully"
            })
            response.encrypt_payload = True      
            return response
        except NotificationLog.DoesNotExist:
            response =  Response({
                "success": False,
                "message": "Notification not found"
            }, status=404)
            response.encrypt_payload = True       
            return response




# # push notification function want to implement later
# def send_push_notification(user, title, message):
#     try:
#         device = FCMDevice.objects.get(user=user)
#         device.send_message(title=title, body=message)
#     except FCMDevice.DoesNotExist:
#         pass  # No device found for user, skip sending notification        
