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



# list all leave requests of all the employees
class LeaveListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leaves = Leave.objects.filter(status="Pending").order_by("-created_at")
        serializer = LeaveSerializer(leaves, many=True)
        return Response({
            "success": True,
            "message": "Leaves retrieved successfully",
            "data": serializer.data
        })



# leave accept , reject by admin api s 
# class LeaveAcceptAPI(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         leave_id = request.data.get("leave_id")
#         if not leave_id:
#             return Response(
#                 {"success": False, "message": "leave_id is required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         leave = get_object_or_404(Leave, id=leave_id)

#         if leave.status != "Pending":
#             return Response(
#                 {"success": False, "message": f"Leave already {leave.status.lower()}"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         leave.status = "Approved"
#         leave.approved_by = request.user
#         leave.save()

#         # Send notification to the employee who applied for leave
#         if leave.user:
#             NotificationLog.objects.create(
#                 user=leave.user,
#                 action=f"Your leave request for {leave.leave_type} from {leave.start_date} to {leave.end_date} has been approved by {request.user.email}",
#                 title = "Leave Approved"
#             )

#         return Response(
#             {"success": True, "message": "Leave request approved successfully"},
#             status=status.HTTP_200_OK,
#         )

class LeaveAcceptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        if request.user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Access denied. Only admins can approve leaves.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        leave_id = request.data.get("leave_id")
        if not leave_id:
            return Response(
                {"success": False, "message": "leave_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave = get_object_or_404(Leave, id=leave_id)

        # Prevent re-approval or re-rejection
        # if leave.status != "Pending":
        #     return Response(
        #         {"success": False, "message": f"Leave already {leave.status.lower()}"},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        approver = request.user
        employee_profile = getattr(approver, "employee_profile", None)
        approver_role = getattr(approver, "role", None)
        approver_user_type = getattr(employee_profile, "user_type", "")
        approver_designation = getattr(employee_profile, "designation", "")

        # Convert to lowercase for matching
        approver_user_type = approver_user_type.lower() if approver_user_type else ""
        approver_designation = approver_designation.lower() if approver_designation else ""

        #  Determine approver level (either user_type OR designation)
        approver_type = approver_user_type or approver_designation

        # Mark approval fields and reset corresponding rejection flags
        # if approver_role in ["admin", "superadmin"]:
        #     leave.is_team_lead_approved = True
        #     leave.is_project_leader_approved = True
        #     leave.is_hr_approved = True
        #     leave.is_ceo_approved = True
        #     leave.is_team_lead_rejected = False
        #     leave.is_project_leader_rejected = False
        #     leave.is_hr_rejected = False
        #     leave.is_ceo_rejected = False

        if approver_user_type in ["team lead", "teamlead"] or approver_designation in ["team lead", "teamlead"]:
            leave.is_team_lead_approved = True
            leave.is_team_lead_rejected = False

        elif approver_user_type in ["project lead", "projectlead"] or approver_designation in ["project lead", "projectlead"]:
            leave.is_project_leader_approved = True
            leave.is_project_leader_rejected = False

        elif approver_user_type == "hr" or approver_designation == "hr":
            leave.is_hr_approved = True
            leave.is_hr_rejected = False

        elif approver_user_type == "ceo" or approver_designation == "ceo":
            leave.is_ceo_approved = True
            leave.is_ceo_rejected = False

        #  Overall leave becomes Approved
        leave.status = "Approved"
        leave.approved_by = approver
        leave.save()

        #  Notify employee
        if leave.user:
            NotificationLog.objects.create(
                user=leave.user,
                title="Leave Approved",
                action=(
                    f"Your leave request for {leave.leave_type} "
                    f"({leave.start_date} to {leave.end_date}) "
                    f"has been approved by {approver.email}"
                ),
            )

        return Response(
            {
                "success": True,
                "message": (
                    f"Leave approved successfully by "
                    f"{approver_type or approver_role or approver.email}"
                ),
            },
            status=status.HTTP_200_OK,
        )


# class LeaveRejectAPI(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         leave_id = request.data.get("leave_id")
#         rejection_reason = request.data.get("rejection_reason", None)

#         if not leave_id:
#             return Response(
#                 {"success": False, "message": "leave_id is required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         leave = get_object_or_404(Leave, id=leave_id)

#         if leave.status != "Pending":
#             return Response(
#                 {"success": False, "message": f"Leave already {leave.status.lower()}"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         leave.status = "Rejected"
#         leave.approved_by = request.user
#         if rejection_reason:
#             leave.rejection_reason = rejection_reason  
#         leave.save()

#         # Send notification to the employee who applied for leave
#         if leave.user:
#             notification_message = f"Your leave request for {leave.leave_type} from {leave.start_date} to {leave.end_date} has been rejected by {request.user.email}"
#             if rejection_reason:
#                 notification_message += f". Reason: {rejection_reason}"
            
#             NotificationLog.objects.create(
#                 user=leave.user,
#                 action=notification_message,
#                 title = "Leave Rejected"
#             )

#         return Response(
#             {"success": True, "message": "Leave request rejected successfully"},
#             status=status.HTTP_200_OK,
#         )
class LeaveRejectAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        leave_id = request.data.get("leave_id")
        rejection_reason = request.data.get("rejection_reason", None)

        if not leave_id:
            return Response(
                {"success": False, "message": "leave_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave = get_object_or_404(Leave, id=leave_id)

        rejector = request.user
        employee_profile = getattr(rejector, "employee_profile", None)
        rejector_role = getattr(rejector, "role", None)
        rejector_user_type = getattr(employee_profile, "user_type", None)
        rejector_designation = getattr(employee_profile, "designation", None)
        rejector_user_type = rejector_user_type.lower() if rejector_user_type else ""
        rejector_designation = rejector_designation.lower() if rejector_designation else ""
        rejector_type = rejector_user_type or rejector_designation

        
        # rejector
        # Handle rejection logic dynamically
        # if rejector_role in ["admin", "superadmin"]:
        #     leave.is_team_lead_rejected = True
        #     leave.is_project_leader_rejected = True
        #     leave.is_hr_rejected = True
        #     leave.is_ceo_rejected = True

        #     # reset approvals
        #     leave.is_team_lead_approved = False
        #     leave.is_project_leader_approved = False
        #     leave.is_hr_approved = False
        #     leave.is_ceo_approved = False

        if rejector_user_type in ["team lead", "teamlead"] or rejector_designation in ["team lead","teamlead"]:
            leave.is_team_lead_rejected = True
            leave.is_team_lead_approved = False

        elif rejector_user_type in ["project lead" , "projectlead"] or rejector_designation in ["project lead" , "projectlead"]:
            leave.is_project_leader_rejected = True
            leave.is_project_leader_approved = False

        elif rejector_user_type == "hr" or rejector_designation == "hr":
            leave.is_hr_rejected = True
            leave.is_hr_approved = False

        elif rejector_user_type == "ceo" or rejector_designation == "ceo":
            leave.is_ceo_rejected = True
            leave.is_ceo_approved = False

        #  Always set status to Rejected even if previously approved
        leave.status = "Rejected"
        leave.approved_by = rejector
        if rejection_reason:
            leave.rejection_reason = rejection_reason
        leave.save()

        # Notify the employee
        if leave.user:
            notification_message = (
                f"Your leave request for {leave.leave_type} "
                f"({leave.start_date} to {leave.end_date}) "
                f"has been rejected by {rejector.email}"
            )
            if rejection_reason:
                notification_message += f". Reason: {rejection_reason}"

            NotificationLog.objects.create(
                user=leave.user,
                title="Leave Rejected",
                action=notification_message,
            )

        return Response(
            {
                "success": True,
                "message": (
                    f"Leave rejected successfully by "
                    f"{rejector_type or rejector_role or rejector.email}"
                ),
            },
            status=status.HTTP_200_OK,
        )

#  leave work flow diagram
# class LeavediagramAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk):
#         leave = get_object_or_404(Leave, pk=pk)
#         serializer = LeavediagramSerializer(leave)
#         return Response({
#             "success": True,
#             "message": "Leave details retrieved successfully",
#             "data": serializer.data
#         }, status=status.HTTP_200_OK)
class LeavediagramAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        """
        Get the most recent leave for a specific employee by EmployeeDetail.pk
        (ordered by created_at DESC)
        """
        employee = get_object_or_404(EmployeeDetail, pk=employee_id)

        # Get only the latest leave
        latest_leave = Leave.objects.filter(employee=employee).order_by('-created_at').first()

        if not latest_leave:
            return Response({
                "success": False,
                "message": f"No leave records found for employee {employee.first_name} {employee.last_name}",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = LeavediagramSerializer(latest_leave)
        return Response({
            "success": True,
            "message": f"Most recent leave record for employee {employee.first_name} {employee.last_name}",
            "employee_id": employee.id,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
# employee details with leave details
class EmployeeDetailWithLeave(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_object_or_404(EmployeeDetail, pk=pk)
        serializer = EmployeeDetailWithLeaveSerializer(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })

# holiday adding api
class HolidayCreateView(APIView):
    permission_classes = [IsAuthenticated]

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
        data = request.data.copy()
        if not data.get("type"):
            data["type"] = "company"   

        serializer = HolidaySerializer1(data=data)
        if serializer.is_valid():
            serializer.save(added_by=request.user)
            return Response({
                "success": True,
                "message": "Holiday created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)