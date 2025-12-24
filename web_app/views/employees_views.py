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




# list employees based on company branch id
class EmployeeListByBranchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,branch_id):
        # Check if branch exists
        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({
                "success": False,
                "message": f"Branch '{branch_id}' not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Get employees in this branch
        employees = EmployeeDetail.objects.filter(branch=branch)
        serializer = EmployeeSerializer(employees, many=True)

        return Response({
            "success": True,
            "message": f"Employees in branch '{branch_id}' fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)



# employ7ee profile edit api
class EmployeeDetailEdit(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_object_or_404(EmployeeDetail, pk=pk)
        serializer = EmployeeDetaileditSerializer(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })

    def put(self, request, pk):
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
        employee = get_object_or_404(EmployeeDetail, pk=pk)
        serializer = EmployeeDetaileditSerializer(employee, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # ✅ Identify updated fields
            updated_fields = list(serializer.validated_data.keys())

            # ✅ Build response for updated fields
            filtered_response = {}

            for field in updated_fields:
                if field == "bank_details":
                    # Fetch latest updated bank details
                    bank_qs = BankDetail.objects.filter(employee=employee)
                    filtered_response["bank_details"] = BankDetailSerializer(bank_qs, many=True).data
                elif field in serializer.data:
                    filtered_response[field] = serializer.data[field]

            return Response({
                "status": True,
                "message": "Employee and bank details updated successfully.",
                "updated_data": filtered_response
            }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# company employee list api
class EmployeeListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"status": "failed", "message": "You are not authorized to see the list"},
                status=status.HTTP_403_FORBIDDEN,
            )

        employees = EmployeeDetail.objects.filter(user__is_active=True).order_by('-created_at')
        serializer = EmployeeDetailSerializer(employees, many=True)
        return Response(
            {
                'message': 'Employees listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )



#  list of some employee user_types for adding the project 

class TeamLeaderListAPIView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        team_leaders = EmployeeDetail.objects.filter(user_type__exact="Team leader")
        serializer = FilterNameSerializer(team_leaders, many=True)
        return Response(
            {
                'message': 'Team leaders listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
        
        # list project manager for adding the project
class ProjectmanagerListAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        project_managers = EmployeeDetail.objects.filter(user_type__iexact="Project Manager")
        serializer = ProjectManagerNameSerializer(project_managers, many=True)
        return Response(
            {
                'message': 'Project managers listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
        
        
class EmployeeListAPIView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        Employee = EmployeeDetail.objects.filter(user__role__iexact="employee")
        serializer = EmployeeNameSerializer(Employee, many=True)
        return Response(
            {
                'message': 'Employee listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )

# project members list by employee id 

class ProjectMembersListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
       
        employee = get_object_or_404(EmployeeDetail, id=employee_id)
        user_id = employee.user.id  # linked user id

      
        members = ProjectMembers.objects.select_related('project').all()

        filtered_members = []
        for member in members:
           
            is_team_leader = (
                isinstance(member.team_leader, dict)
                and member.team_leader.get("id") == user_id
            )
            is_project_manager = (
                isinstance(member.project_manager, dict)
                and member.project_manager.get("id") == user_id
            )
            is_team_member = (
                isinstance(member.tags, list)
                and any(
                    isinstance(tag, dict) and tag.get("id") == user_id
                    for tag in member.tags
                )
            )

            if is_team_leader or is_project_manager or is_team_member:
                filtered_members.append(member)

        serializer = ProjectMemberslistSerializer(filtered_members, many=True)

      
        formatted_data = []
        for item in serializer.data:
            project_members = []

            team_leader = item.get("team_leader")
            if isinstance(team_leader, dict):
                project_members.append(team_leader)

            project_manager = item.get("project_manager")
            if isinstance(project_manager, dict):
                project_members.append(project_manager)

            tags = item.get("tags")
            if isinstance(tags, list):
                project_members.extend(
                    [tag for tag in tags if isinstance(tag, dict)]
                )

         
            unique_members = {
                m["id"]: m for m in project_members if isinstance(m, dict) and "id" in m
            }.values()

         
            detailed_members = []
            for m in unique_members:
                try:
                    emp = EmployeeDetail.objects.select_related("user").get(user__id=m["id"])
                    detailed_members.append({
                        "id": m["id"],
                        "name": emp.user.first_name + " " + emp.user.last_name or emp.user.username,
                        "email": emp.user.email,
                        "designation": emp.designation if hasattr(emp, "designation") else None,
                        "phone_number": emp.phone if hasattr(emp, "phone") else None,
                        "profile_pic": (
                            request.build_absolute_uri(emp.profile_pic.url)
                            if getattr(emp, "profile_pic", None) else None
                        ),
                    })
                except EmployeeDetail.DoesNotExist:
              
                    detailed_members.append({
                        "id": m["id"],
                        "name": m.get("name"),
                        "email": m.get("email"),
                        "designation": None,
                        "phone_number": None,
                        "profile_pic": None,
                    })

            formatted_data.append({
                "project_id": item.get("id"),
                "project_name": item.get("project_name"),
                "members": detailed_members,
            })

        return Response(
            {
                "status": True,
                "message": "Project members fetched successfully.",
                "data": formatted_data,
            },
            status=status.HTTP_200_OK,
        )


# get employee details by employe id 
class EmployeeDetailsById(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, emp_id):
        employee = EmployeeDetail.objects.get(id = emp_id)
        serializer = EmployeeDetailSerializer(employee=employee)
        return Return({

            "success":""
        })
        pass




# admin view employees list  all employees list   
class EmployeeListadminView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        employees = EmployeeDetail.objects.filter(user__is_active=True)
        serializer = EmployeeListSerializerAdminView(employees, many=True, context={"today": today})
        return Response({
            "status": True,
            "message": "Data fetched successfully",
            "data": serializer.data
        })

# counts of employees based on designation 
class EmployeeCountByDesignation(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employees = EmployeeDetail.objects.all()
        designation_counts = {}

        for emp in employees:
            decrypted_designation = decrypt_value(emp.designation).strip() if emp.designation else "Not Specified"
            designation_counts[decrypted_designation] = designation_counts.get(decrypted_designation, 0) + 1

        result = [
            {"designation": designation, "count": count}
            for designation, count in sorted(designation_counts.items())
        ]

        return Response({
            "success": True,
            "message": "Employee counts by designation",
            "data": result
        }, status=status.HTTP_200_OK)

# todays employee count by designation

class TodayEmployeeCountByDesignation(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

     
        attendance_today = (
            Attendance.objects
            .filter(date=today, punch_in=True)
            .values("employee__designation", "employee") 
            .distinct()  
        )

       
        designation_counts = {}
        for entry in attendance_today:
            designation = entry["employee__designation"] or "Not Specified"
            designation_counts[designation] = designation_counts.get(designation, 0) + 1

        result = [
            {"designation": designation, "count": count}
            for designation, count in designation_counts.items()
        ]

        return Response({
            "success": True,
            "message": f"Today's employee counts by designation ({today})",
            "data": result
        })


# ADMIN Filter employee designation wise list       
class EmployeeListAdminFilteredView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        today = date.today()
        designation = request.query_params.get("designation")
        

        employees = EmployeeDetail.objects.all()

 
        if designation:
            employees = employees.filter(designation__iexact=designation)
       
        serializer = EmployeeListSerializerAdminView(
            employees,
            many=True,
            context={"today": today}
        )

        return Response({
            "status": True,
            "message": "Data fetched successfully",
            "count": employees.count(),
            "data": serializer.data
        })



# all  active employee count
class ActiveEmployeeCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_employee_count = EmployeeDetail.objects.filter(user__is_active=True).count()
        return Response({
            "status": True,
            "message": "Active employee count fetched successfully",
            "active_employee_count" : active_employee_count
        })
    



# api for temporary removing employee from the system
class RemoveEmployeeAPIView(APIView):
    """
    API to temporarily remove an employee from the system (soft delete) 
    with exit status and exit date.
    """
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
        user = request.user
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to remove employees."},
                status=status.HTTP_403_FORBIDDEN
            )

        employee_id = request.data.get("employee_id")
        emp_status =  request.data.get("emp_status")  # e.g., "Resignation", "Termination"
        reason =  request.data.get("reason")


        if not employee_id:
            return Response(
                {"success": False, "message": "employee_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not emp_status:
            return Response(
                {"success": False, "message": "emp_status is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employee = EmployeeDetail.objects.get(user=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response(
                {"success": False, "message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND
            )

      
        employee.is_active = False
        employee.emp_status = emp_status
        employee.emp_exit_date = timezone.now().date()
        employee.removing_reason = reason
        employee.save()

    
        if employee.user:
            employee.user.is_active = False
            employee.user.save()

           
            try:
                tokens = OutstandingToken.objects.filter(user=employee.user)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
            except Exception as e:
                print("Token blacklisting error:", e)

        # Log the removal action
        NotificationLog.objects.create(
            user=user,
            title = "Employee Removed",
            action=f"Removed employee '{employee.first_name} {employee.last_name}' "
                   f"(ID: {employee.employee_id}) with status '{emp_status}'"
        )

        return Response(
            {"success": True, "message": "Employee removed successfully with status and exit date."},
            status=status.HTTP_200_OK
        )

# api for reactivating removed employee
class ReactivateEmployeeAPIView(APIView):
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
        user = request.user

        # Only admin/superadmin can reactivate
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to reactivate employees."},
                status=status.HTTP_403_FORBIDDEN
            )

        employee_id =  request.data.get("employee_id")
        emp_status = request.data.get("emp_status")  # e.g., "Resignation", "Termination"

        if not employee_id:
            return Response(
                {"success": False, "message": "employee_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employee = EmployeeDetail.objects.get(user=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response(
                {"success": False, "message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if employee user exists
        if not employee.user:
            return Response(
                {"success": False, "message": "This employee does not have a linked user account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is already active
        if employee.user.is_active:
            return Response(
                {"success": False, "message": "Employee is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reactivate user account
        employee.user.is_active = True
        employee.user.save()

      
        try:
            tokens = OutstandingToken.objects.filter(user=employee.user)
            for token in tokens:
                BlacklistedToken.objects.filter(token=token).delete()
        except Exception as e:
            print("Token cleanup error:", e)

        # Update employee status if provided
        if emp_status:
            employee.emp_status = emp_status
        employee.save()

        # Log reactivation
        NotificationLog.objects.create(
            user=user,
            title="Employee Reactivated",
            action=f"Reactivated employee '{employee.first_name} {employee.last_name}' (ID: {employee.employee_id})"
        )

        return Response(
            {"success": True, "message": "Employee reactivated successfully."},
            status=status.HTTP_200_OK
        )


# list all inactive employeees in the user system employee model have no is_active  contain in user model
class InactiveEmployeeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inactive_employees = EmployeeDetail.objects.filter(user__is_active=False)
        serializer = EmployeeActiveInactiveListSerializer(inactive_employees, many=True)
        return Response({
            "success": True,
            "message": "Inactive employees fetched successfully",
            "data": serializer.data
        })
    

# list all active employees
class ActiveEmployeeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_employees = EmployeeDetail.objects.filter(user__is_active=True)
        serializer = EmployeeActiveInactiveListSerializer(active_employees, many=True)
        return Response({
            "success": True,
            "message": "Active employees fetched successfully",
            "data": serializer.data
        })

# search inactive employees by first_name and last_name 
class InactiveEmployeeSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("letters", "").strip()

        if not query:
            return Response({
                "success": False,
                "message": "Query parameter 'letters' is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert query to lowercase for case-insensitive matching
        query = query.lower()

        # Get all inactive employees
        inactive_employees = EmployeeDetail.objects.filter(user__is_active=False)

        matched = []
        for emp in inactive_employees:
            first_name = decrypt_value(emp.first_name).strip()
            last_name = decrypt_value(emp.last_name).strip()

            if query in first_name.lower() or query in last_name.lower():
                emp.first_name = first_name
                emp.last_name = last_name
                matched.append(emp)

        serializer = EmployeeActiveInactiveListSerializer(matched, many=True)

        return Response({
            "success": True,
            "message": "Inactive employees searched successfully.",
            "count": len(matched),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    

    # search active employees
class ActiveEmployeeSearchListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Normalize the letter to lowercase (handle capital input)
        letter = (kwargs.get("letters") or request.GET.get("letters") or "").strip().lower()

        queryset = EmployeeDetail.objects.filter(user__is_active=True)

        matched = []

        # Decrypt and filter manually
        for emp in queryset:
            first_name = decrypt_value(emp.first_name).strip()
            last_name = decrypt_value(emp.last_name).strip()

            # Compare in lowercase (case-insensitive)
            if not letter or first_name.lower().startswith(letter) or last_name.lower().startswith(letter):
                emp.first_name = first_name  # keep original case for display
                emp.last_name = last_name
                matched.append(emp)


        matched = sorted(matched, key=lambda x: x.first_name.lower())

        serializer = EmployeeActiveInactiveListSerializer(matched, many=True)

        return Response({
            "success": True,
            "message": "Active employee list fetched successfully",
            "count": len(matched),
            "employees": serializer.data
        }, status=status.HTTP_200_OK)


# recent activities
class EmployeeActivityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        latest_leave_today = Leave.objects.filter(
            employee=OuterRef('pk'),
            created_at__date=today
        ).order_by('-created_at')

        employees_with_leave = EmployeeDetail.objects.annotate(
            leave_status=Subquery(latest_leave_today.values('status')[:1]),
            latest_leave_applied_on=Subquery(latest_leave_today.values('created_at')[:1])
        ).filter(leave_status__isnull=False)

        # --- Employees added today ---
        new_employees_today = EmployeeDetail.objects.filter(created_at__date=today)

        # --- Employees removed today ---
        removed_employees_today = EmployeeDetail.objects.filter(
            user__is_active=False,
            updated_at__date=today
        )

        # --- New projects added today ---
        new_projects_today = Project.objects.filter(created_at__date=today)

        # --- Projects updated today ---
        updated_projects_today = Project.objects.filter(
            updated_at__date=today
        ).exclude(created_at__date=today)  # exclude those already counted as new

        # --- New tasks added today ---
        new_tasks_today = Task.objects.filter(created_at__date=today)

        # --- Attendance updated today ---
        attendance_updated_today = Attendance.objects.filter(updated_at__date=today)

        employee_activities = []
        IST = pytz.timezone("Asia/Kolkata")
        # --- Employee leaves ---
        for emp in employees_with_leave:
            if emp.latest_leave_applied_on:
                activity_time = timezone.localtime(emp.latest_leave_applied_on, IST)
                employee_activities.append({
                    "type": "Employee",
                    "id": emp.id,
                    "employee_id": emp.employee_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "designation": emp.designation,
                    "activity_type": f"Leave Applied ({emp.leave_status})",
                    "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                })

        # --- New employees ---
        for emp in new_employees_today:
            activity_time = timezone.localtime(emp.created_at, IST)
            employee_activities.append({
                "type": "Employee",
                "id": emp.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "designation": emp.designation,
                "activity_type": "New Employee Added",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- Removed employees ---
        for emp in removed_employees_today:
            activity_time = timezone.localtime(emp.updated_at, IST)
            employee_activities.append({
                "type": "Employee",
                "id": emp.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "designation": emp.designation,
                "activity_type": "Employee Deleted",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- New projects ---
        for proj in new_projects_today:
            activity_time = timezone.localtime(proj.created_at, IST)
            employee_activities.append({
                "type": "Project",
                "id": proj.id,
                "project_name": proj.project_name,
                "client": proj.client,
                "assigned_by": proj.assigned_by.first_name if proj.assigned_by else None,
                "priority": proj.priority,
                "status": proj.status,
                "activity_type": "New Project Added",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- Updated projects ---
        for proj in updated_projects_today:
            activity_time = timezone.localtime(proj.updated_at, IST)
            employee_activities.append({
                "type": "Project",
                "id": proj.id,
                "project_name": proj.project_name,
                "client": proj.client,
                "priority": proj.priority,
                "assigned_by": proj.assigned_by.first_name if proj.assigned_by else None,
                "status": proj.status,
                "activity_type": "Project Updated",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- New tasks ---
        for task in new_tasks_today:
            activity_time = timezone.localtime(task.created_at, IST)
            assigned_to_users = task.assigned_to.all()
            assigned_to_list = [f"{u.first_name} {u.last_name}" for u in assigned_to_users]

            employee_activities.append({
                "type": "Task",
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "project_name": task.project.project_name if task.project else None,
                "assigned_by": task.assigned_by.first_name if task.assigned_by else None,
                "assigned_to": assigned_to_list,
                "status": task.status,
                "activity_type": "New Task Created",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- Attendance updated ---
        for att in attendance_updated_today:
            emp = att.employee
            activity_time = timezone.localtime(att.updated_at, IST)
            employee_activities.append({
                "type": "Attendance",
                "id": att.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "activity_type": "Attendance Updated",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- Sort by latest activity time ---
        employee_activities.sort(key=lambda x: x['activity_time'], reverse=True)

        return Response({
            "success": True,
            "count": len(employee_activities),
            "activities": employee_activities
        })

#  last 7 days activity list api
class Last7DaysActivityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seven_days_ago = timezone.now() - timedelta(days=7)
        IST = pytz.timezone("Asia/Kolkata")

        activities = []

        # --- Employee leaves in last 7 days ---
        leaves = Leave.objects.filter(created_at__gte=seven_days_ago).select_related('employee')
        for leave in leaves:
            activity_time = timezone.localtime(leave.created_at, IST)
            activities.append({
                "type": "Employee",
                "id": leave.employee.id,
                "employee_id": leave.employee.employee_id,
                "first_name": leave.employee.first_name,
                "last_name": leave.employee.last_name,
                "designation": leave.employee.designation,
                "activity_type": f"Leave Applied ({leave.status})",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- New employees added in last 7 days ---
        new_employees = EmployeeDetail.objects.filter(created_at__gte=seven_days_ago)
        for emp in new_employees:
            activity_time = timezone.localtime(emp.created_at, IST)
            activities.append({
                "type": "Employee",
                "id": emp.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "designation": emp.designation,
                "activity_type": "New Employee Added",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- Employees removed in last 7 days ---
        removed_employees = EmployeeDetail.objects.filter(
            user__is_active=False,
            updated_at__gte=seven_days_ago
        )
        for emp in removed_employees:
            activity_time = timezone.localtime(emp.updated_at, IST)
            activities.append({
                "type": "Employee",
                "id": emp.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "designation": emp.designation,
                "activity_type": "Employee Deleted",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })

        # --- New projects added in last 7 days ---
        new_projects = Project.objects.filter(created_at__gte=seven_days_ago)
        for proj in new_projects:
            activity_time = timezone.localtime(proj.created_at, IST)
            activities.append({
                "type": "Project",
                "id": proj.id,
                "project_name": proj.project_name,
                "client": proj.client,
                "assigned_by": proj.assigned_by.first_name if proj.assigned_by else None,
                "priority": proj.priority,  
                "status": proj.status,
                "activity_type": "New Project Added",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })
        # --- Projects updated in last 7 days ---
        updated_projects = Project.objects.filter(
            updated_at__gte=seven_days_ago
        ).exclude(created_at__gte=seven_days_ago)  # exclude those already counted as new
        for proj in updated_projects:
            activity_time = timezone.localtime(proj.updated_at, IST)
            activities.append({
                "type": "Project",
                "id": proj.id,
                "project_name": proj.project_name,
                "client": proj.client,
                "assigned_by": proj.assigned_by
                .first_name if proj.assigned_by else None,
                "priority": proj.priority,
                "status": proj.status,
                "activity_type": "Project Updated",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })
        # --- New tasks added in last 7 days ---
        new_tasks = Task.objects.filter(created_at__gte=seven_days_ago) 
        for task in new_tasks:
            activity_time = timezone.localtime(task.created_at, IST)
            assigned_to_users = task.assigned_to.all()
            assigned_to_list = [f"{u.first_name} {u.last_name}" for u in assigned_to_users]
            activities.append({
                "type": "Task",
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "project_name": task.project.project_name if task.project else None,
                "assigned_by": task.assigned_by.first_name if task.assigned_by else None,
                "assigned_to": assigned_to_list,
                "status": task.status,
                "activity_type": "New Task Created",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })
        # --- Attendance updated in last 7 days ---
        attendances = Attendance.objects.filter(updated_at__gte=seven_days_ago).select_related('employee')
        for att in attendances:
            emp = att.employee
            activity_time = timezone.localtime(att.updated_at, IST)
            activities.append({
                "type": "Attendance",
                "id": att.id,
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "activity_type": "Attendance Updated",
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            })
        # --- Sort by latest activity time ---
        activities.sort(key=lambda x: x['activity_time'], reverse=True)
        return Response({
            "success": True,
            "count": len(activities),
            "activities": activities
        })
    

# employee work hour summary api
# class EmployeeWorkHourSummaryAPI(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, employee_id):
#         try:
#             employee = EmployeeDetail.objects.get(id=employee_id)
#         except EmployeeDetail.DoesNotExist:
#             return Response({
#                 "success": False,
#                 "message": "Employee not found."
#             }, status=status.HTTP_404_NOT_FOUND)

#         # ------------------------------

#         # ------------------------------
#         def calculate_work_hours_per_day(records):
#             """
#             For each date, get the earliest in_time and latest out_time,
#             then sum total worked hours.
#             """
#             total_hours = 0
#             overtime_hours = 0

#             grouped = (
#                 records.values("date")
#                 .annotate(first_in=Min("in_time"), last_out=Max("out_time"))
#                 .order_by("date")
#             )

#             for entry in grouped:
#                 in_time = entry["first_in"]
#                 out_time = entry["last_out"]
#                 if in_time and out_time:
#                     diff = (out_time - in_time).total_seconds() / 3600
#                     total_hours += diff
#                     if diff > 8:
#                         overtime_hours += (diff - 8)
#             return round(total_hours, 2), round(overtime_hours, 2)

#         # ------------------------------

#         # ------------------------------
#         today = timezone.localdate()
#         start_of_week = today - timedelta(days=today.weekday())  # Monday
#         start_of_month = today.replace(day=1)

#         # ------------------------------
     
#         # ------------------------------
#         today_records = Attendance.objects.filter(employee=employee, date=today)
#         week_records = Attendance.objects.filter(employee=employee, date__gte=start_of_week, date__lte=today)
#         month_records = Attendance.objects.filter(employee=employee, date__gte=start_of_month, date__lte=today)

#         # ------------------------------
#         # ⏱ Calculate Hours
#         # ------------------------------
#         total_hours_today, overtime_today = calculate_work_hours_per_day(today_records)
#         total_hours_week, overtime_week = calculate_work_hours_per_day(week_records)
#         total_hours_month, overtime_month = calculate_work_hours_per_day(month_records)

#         # Expected hours = 8 * number of working days
#         expected_today = 8
#         expected_week = week_records.values("date").distinct().count() * 8
#         expected_month = month_records.values("date").distinct().count() * 8


#         # ------------------------------
#         return Response({
#             "success": True,
#             "message": "Work hour summary fetched successfully.",
#             "employee_id": employee.id,
#             "employee_name": employee.user.first_name if employee.user else None,
#             "summary": {
#                 "today": f"{total_hours_today}/{expected_today} hrs",
#                 "week": f"{total_hours_week}/{expected_week} hrs",
#                 "month": f"{total_hours_month}/{expected_month} hrs",
#                 "overtime_month": f"{overtime_month} hrs"
#             },
#             # "raw_data": {
#             #     "total_hours_today": total_hours_today,
#             #     "total_hours_week": total_hours_week,
#             #     "total_hours_month": total_hours_month,
#             #     "overtime_today": overtime_today,
#             #     "overtime_week": overtime_week,
#             #     "overtime_month": overtime_month
#             # }
#         }, status=status.HTTP_200_OK)
# employee work hour summary api
class EmployeeWorkHourSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # --------------------------------
        def calculate_work_hours_per_day(records):
            total_hours = 0
            overtime_hours = 0
            standard_hours = 8

            grouped = (
                records.values("date")
                .annotate(first_in=Min("in_time"), last_out=Max("out_time"))
                .order_by("date")
            )

            for entry in grouped:
                in_time = entry["first_in"]
                out_time = entry["last_out"]

                if in_time and out_time:

              
                    if out_time < in_time:
                        out_time = out_time + timedelta(days=1)

                    diff = (out_time - in_time).total_seconds() / 3600
                    total_hours += diff

                    if diff > standard_hours:
                        overtime_hours += (diff - standard_hours)

            return round(total_hours, 2), round(overtime_hours, 2)

        # --------------------------------
        today = timezone.localdate()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        start_of_month = today.replace(day=1)

        today_records = Attendance.objects.filter(employee=employee, date=today)
        week_records = Attendance.objects.filter(employee=employee, date__gte=start_of_week, date__lte=today)
        month_records = Attendance.objects.filter(employee=employee, date__gte=start_of_month, date__lte=today)

        total_hours_today, overtime_today = calculate_work_hours_per_day(today_records)
        total_hours_week, overtime_week = calculate_work_hours_per_day(week_records)
        total_hours_month, overtime_month = calculate_work_hours_per_day(month_records)

        expected_today = 8
        expected_week = week_records.values("date").distinct().count() * 8
        expected_month = month_records.values("date").distinct().count() * 8

        return Response({
            "success": True,
            "message": "Work hour summary fetched successfully.",
            "employee_id": employee.id,
            "employee_name": employee.user.first_name if employee.user else None,
            "summary": {
                "today": f"{total_hours_today}/{expected_today} hrs",
                "week": f"{total_hours_week}/{expected_week} hrs",
                "month": f"{total_hours_month}/{expected_month} hrs",
                "overtime_month": f"{overtime_month} hrs"
            }
        }, status=status.HTTP_200_OK)


# employee todays work hours summary
class EmployeeDailyProductivity(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        today = now().date()

        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Employee not found."
            }, status=404)

        attendance_qs = Attendance.objects.filter(employee=employee, date=today)

        if not attendance_qs.exists():
            return Response({
                "success": True,
                "message": "No attendance records found for today.",
                "employee_id": employee_id,
                "date": str(today),
                "data": {
                    "total_working_hours": 0,
                    "break_hours": 0,
                    "productive_hours": 0,
                    "overtime_hours": 0
                }
            })

        # Get first punch-in and last punch-out for today
        attendance_summary = attendance_qs.aggregate(
            first_in=Min('in_time'),
            last_out=Max('out_time')
        )

        first_in = attendance_summary['first_in']
        last_out = attendance_summary['last_out']

        if not first_in:
            return Response({
                "success": True,
                "message": "Incomplete attendance record (no punch-in found).",
                "employee_id": employee_id,
                "date": str(today),
                "data": {
                    "total_working_hours": 0,
                    "break_hours": 0,
                    "productive_hours": 0,
                    "overtime_hours": 0
                }
            })

        # If no punch-out, consider current time
        if not last_out:
            last_out = now()

      
        if last_out < first_in:
            last_out = last_out + timedelta(days=1)

        # Calculate working durations
        total_worked = last_out - first_in
        standard_work = timedelta(hours=8, minutes=30)
        break_time = timedelta(hours=1)

        productive_time = total_worked - break_time if total_worked > break_time else timedelta(0)
        overtime = total_worked - standard_work if total_worked > standard_work else timedelta(0)

        # Convert timedelta to hours
        def td_to_hours(td):
            return round(td.total_seconds() / 3600, 2)

        response_data = {
            "total_working_hours": td_to_hours(total_worked),
            "break_hours": td_to_hours(break_time),
            "productive_hours": td_to_hours(productive_time),
            "overtime_hours": td_to_hours(overtime)
        }

        return Response({
            "success": True,
            "message": "Today's productivity fetched successfully.",
            "employee_id": employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "date": str(today),
            "data": response_data
        })