from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core_app.models import EmployeeGoogleFormResponse

from web_app.serializers import *
import io
import os
from django.core.files import File
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view


@api_view(['POST'])
def google_form_submit(request):
    data = request.data

    # Use the serializer to validate and save the incoming data
    serializer = EmployeeGoogleFormSerializer(data=data)

    if serializer.is_valid():
        # If valid, save the model instance to the database
        serializer.save()
        return Response({
            "status": True,
            "message": "Google Form data saved successfully", # Success message for Apps Script
            "data": serializer.data
        }, status=status.HTTP_201_CREATED) # HTTP 201 is correct for creation

    # If not valid, return a 400 Bad Request with validation errors
    return Response({
        "status": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)