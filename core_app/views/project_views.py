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




#   login employees daily tasks api       
class EmployeeTasksWithProjectAPI(ListAPIView):
    serializer_class = TaskWithProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(assigned_to=user).select_related('project').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            response =  Response(
                {
                    "success": False,
                    "message": "No tasks found for the logged-in employee.",
                    "data": []
                },
                status=status.HTTP_200_OK
            )
            response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
            return response
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Add summary statistics
        total_tasks = queryset.count()
        pending_tasks = queryset.filter(status="Pending").count()
        in_progress_tasks = queryset.filter(status="In Progress").count()
        completed_tasks = queryset.filter(status="Completed").count()
        
        response = Response(
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
        response.encrypt_payload = True       # 🔥 ONLY LOGIN RESPONSE WILL BE ENCRYPTED
        return response


