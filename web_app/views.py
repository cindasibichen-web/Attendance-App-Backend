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
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from . serializers import *
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
from drf_spectacular.utils import extend_schema




# proile details of login admin
# Admin profile view        
class AdminProfileView(RetrieveAPIView):
    serializer_class = AdminProfileSerializerView
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Optional: Only allow admin roles
        if user.role != 'admin' and user.role != 'superadmin':
            return Response(
                {
                    "success": "False",
                    "message": "Access denied. Only admins can access this profile.",
                    "data": {}
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(user)
        return Response(
            {
                "success": "True",
                "message": "Admin profile fetched successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

# get count of total pending project approvals and also total pending leave approvals
class DashboardPendingApprovalsCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to view this data."},
                status=status.HTTP_403_FORBIDDEN
            )

        pending_projects_count = Project.objects.filter(status="Pending").count()
        pending_leaves_count = Leave.objects.filter(status="Pending").count()

        return Response({
            "success": True,
            "message": "Pending approvals count fetched successfully.",
            "data": {
                "pending_projects": pending_projects_count,
                "pending_leaves": pending_leaves_count
            }
        }, status=status.HTTP_200_OK)



class TaskPercentageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_task = Task.objects.count()

        # Avoid division by zero
        if total_task == 0:
            return Response({
                "success": True,
                "message": "No tasks available",
                "data": {
                    "pending": "0%",
                    "on_going": "0%",
                    "completed": "0%",
                    "on_hold": "0%",
                    "overdue": "0%",
                }
            })

        # Count each status
        pending_count = Task.objects.filter(status__iexact="Pending").count()
        on_going_count = Task.objects.filter(status__iexact="On Going").count()
        completed_count = Task.objects.filter(status__iexact="Completed").count()
        on_hold_count = Task.objects.filter(status__iexact="On Hold").count()
        overdue_count = Task.objects.filter(status__iexact="Overdue").count()

        # Helper to format percentage
        def percent(count):
            value = round((count / total_task) * 100, 2)
            return f"{value}%"

        return Response({
            "success": True,
            "total_tasks": total_task,
            "data": {
                "pending": percent(pending_count),
                "on_going": percent(on_going_count),
                "completed": percent(completed_count),
                "on_hold": percent(on_hold_count),
                "overdue": percent(overdue_count),
            }
        })

# add project api 
class AddProjectApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request, *args, **kwargs):
        # Build a plain dict to avoid QueryDict coercing lists/dicts to strings
        data = {}
        for key in request.data.keys():
            data[key] = request.data.get(key)

        # Parse JSON fields (they arrive as strings in multipart)
        for field in ["members", "tasks"]:
            raw_value = data.get(field)
            if isinstance(raw_value, str) and raw_value:
                try:
                    data[field] = json.loads(raw_value)
                except json.JSONDecodeError:
                    return Response({field: ["Invalid JSON."]}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize shapes expected by serializer
        if isinstance(data.get("members"), dict):
            data["members"] = [data["members"]]
        if isinstance(data.get("tasks"), dict):
            data["tasks"] = [data["tasks"]]

        serializer = ProjectSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            project = serializer.save(assigned_by=request.user)
            # --- Create notifications for each assigned task ---
            tasks_data = data.get("tasks", [])
            for task_data in tasks_data:
                assigned_to_id = task_data.get("assigned_to")
                if assigned_to_id:
                    try:
                        assigned_to_user = User.objects.get(id=assigned_to_id)
                        NotificationLog.objects.create(
                            user=assigned_to_user,
                            title = "New Task Assigned",
                            action=f"A new task '{task_data.get('title')}' has been assigned to you in project '{project.project_name}'."
                        )
                    except User.DoesNotExist:
                        pass  # skip if user not found
            return Response({"message": "Project added successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# project patch api
class UpdateProjectApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def patch(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)

        data = {}
        for key in request.data.keys():
            data[key] = request.data.get(key)

        # Parse JSON string fields if needed
        for field in ["members", "tasks"]:
            raw_value = data.get(field)
            if isinstance(raw_value, str) and raw_value:
                try:
                    data[field] = json.loads(raw_value)
                except json.JSONDecodeError:
                    return Response(
                        {field: ["Invalid JSON."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Update main project details
        serializer = ProjectSerializer(project, data=data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()

            # ✅ Incremental update for Members
            if "members" in data:
                for member_data in data["members"]:
                    member_id = member_data.pop("id", None)
                    if member_id:
                        # Update existing
                        member = ProjectMembers.objects.filter(id=member_id, project=project).first()
                        if member:
                            for field, value in member_data.items():
                                setattr(member, field, value)
                            member.save()
                    else:
                        # Create new
                        ProjectMembers.objects.create(project=project, **member_data)

            # ✅ Incremental update for Tasks
            if "tasks" in data:
                for task_data in data["tasks"]:
                    task_id = task_data.pop("id", None)
                    if task_id:
                        task = Task.objects.filter(id=task_id, project=project).first()
                        if task:
                            for field, value in task_data.items():
                                setattr(task, field, value)
                            task.save()
                    else:
                        Task.objects.create(project=project, **task_data)

            return Response(
                {"message": "Project updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
# ✅ Delete project admin by ID 
class DeleteProjectApi(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, project_id, *args, **kwargs):
        project = get_object_or_404(Project, id=project_id)
        project.delete()
        return Response({
            "success": True,
            "message": f"Project with ID {project_id} deleted successfully"
        }, status=status.HTTP_200_OK)


# list projects api
class ListProjectsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        projects = Project.objects.all().order_by("-id")
        serializer = ProjectReadSerializer(projects, many=True)
        return Response({
            "success": True,
            "message": "Projects listed successfully",
            "projects": serializer.data
        }, status=status.HTTP_200_OK)

# project details by project id
class ProjectDetailByIDAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectReadSerializer(project)
        return Response({
            "success": True,
            "message": "Project details retrieved successfully",
            "data": serializer.data
        })


# add  , list  project images to the project
class ProjectImageUploadApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ProjectImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Project image uploaded successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, project_id, *args, **kwargs):
        images = ProjectImages.objects.filter(project__id=project_id)
        serializer = ProjectImageSerializer(images, many=True)
        return Response({
            "success": True,
            "message": f"Images for project ID {project_id} fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    

# image patch delete api 
class ProjectImageDeleteUpdateApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    def patch(self, request, image_id, *args, **kwargs):
        image = get_object_or_404(ProjectImages, id=image_id)
        serializer = ProjectImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Project image updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, image_id, *args, **kwargs):
        image = get_object_or_404(ProjectImages, id=image_id)
        image.delete()
        return Response({
            "success": True,
            "message": f"Project image with ID {image_id} deleted successfully"
        }, status=status.HTTP_200_OK)


class ProjectFileListCreateAPIView(generics.ListCreateAPIView):
    queryset = ProjectFile.objects.all().select_related('project')
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]    
    
    
    
# project id wise get files     
class ProjectFileRetrieveAPIView(generics.ListAPIView):
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return ProjectFile.objects.filter(project__id=project_id).select_related('project')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "data": serializer.data
            })
        else:
            return Response({
                "success": False,
                "message": "No files found"
            })
            
            
            
            
            
class ProjectFileUpdateAPIView(generics.UpdateAPIView):
    queryset = ProjectFile.objects.all()
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # Allow partial update
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "success": True,
            "message": "File updated successfully",
            "data": serializer.data
        })            
 


class ProjectFileDeleteAPIView(generics.DestroyAPIView):
    queryset = ProjectFile.objects.all()
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'  # Delete by ID from URL

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the object to delete
        self.perform_destroy(instance)  # Delete it
        return Response(
            {"success": True, "message": "Deleted successfully"},
            status=status.HTTP_200_OK
        )

    
# add extra tasks to existing project
class AddTasksToProjectApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        project_id = data.get("project_id")
        if not project_id:
            return Response(
                {"project_id": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        project = get_object_or_404(Project, id=project_id)

        # ✅ Handle tasks input (can be list or single object)
        tasks_data = data.get("tasks")

        if not tasks_data:
            return Response(
                {"tasks": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ If tasks_data is a JSON string, parse it
        if isinstance(tasks_data, str):
            try:
                tasks_data = json.loads(tasks_data)
            except json.JSONDecodeError:
                return Response(
                    {"tasks": ["Invalid JSON format."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if isinstance(tasks_data, dict):
            tasks_data = [tasks_data]
        elif not isinstance(tasks_data, list):
            return Response(
                {"tasks": ["This field must be a list or a single object."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_tasks = []
        for task_data in tasks_data:
            task_data["project"] = project.id  

            serializer = TaskSerializer(data=task_data)
            if serializer.is_valid():
                task = serializer.save(project=project,assigned_by=request.user)
                created_tasks.append(task)

                # ✅ Notify assigned user
                assigned_to_id = task_data.get("assigned_to")
                if assigned_to_id:
                    try:
                        assigned_to_user = User.objects.get(id=assigned_to_id)
                        NotificationLog.objects.create(
                            user=assigned_to_user,
                            title="New Task Assigned",
                            action=f"A new task '{task.title}' has been assigned to you in project '{project.project_name}'."
                        )
                    except User.DoesNotExist:
                        pass
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        created_serializer = TaskSerializer(created_tasks, many=True)
        return Response(
            {
                "success": True,
                "message": f"{len(created_tasks)} task(s) added to project '{project.project_name}' successfully.",
                "tasks": created_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )


# edit tasks api 

class EditTaskApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def patch(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, id=task_id)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated_task = serializer.save()

            # Optional: Notify assigned user if assigned_to changed
            if "assigned_to" in request.data:
                try:
                    assigned_user = updated_task.assigned_to
                    NotificationLog.objects.create(
                        user=assigned_user,
                        title="Task Updated",
                        action=f"The task '{updated_task.title}' has been updated."
                    )
                except:
                    pass

            return Response(
                {
                    "success": True,
                    "message": f"Task '{updated_task.title}' updated successfully.",
                 "task": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# delete each tasks from the project
class DeleteTaskApi(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, id=task_id)
        task_title = task.title
        task.delete()

        return Response(
            
            {"success": True,
                "message": f"Task '{task_title}' has been deleted successfully."},
            status=status.HTTP_200_OK
        )


# project accept and reject api 
class AcceptProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        project_id = request.data.get("project_id")
        if not project_id:
            return Response(
                {"success": False, "message": "project_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project = get_object_or_404(Project, id=project_id)

        # Update project status to Accepted
        project.status = "Accepted"
        project.save()

        # Save notification
        NotificationLog.objects.create(
            user=user,
            action=f"Accepted project '{project.project_name}'"
        )

        return Response({
            "success": True,
            "message": f"Project '{project.project_name}' accepted successfully."
        })


class RejectProjectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        project_id = request.data.get("project_id")


        if not project_id:
            return Response(
                {"success": False, "message": "project_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

      
        project = get_object_or_404(Project, id=project_id)

        # Optional reason for rejection from request
        reason_for_rejection = request.data.get("reason_for_rejection", None)

        # Update project status to Rejected
        project.status = "Rejected"
        # Optionally, you can store reason in project if you have a field
        if hasattr(project, "rejection_reason") and reason_for_rejection:
            project.rejection_reason = reason_for_rejection
        project.save()

        # Save notification with optional reason
        action_text = f"Rejected project '{project.project_name}'"
        if reason_for_rejection:
            action_text += f" (Reason: {reason_for_rejection})"

        NotificationLog.objects.create(
            user=user,
            action=action_text
        )

        return Response({
            "success": True,
            "message": f"Project '{project.project_name}' rejected successfully."
        })

# list tasks with all details
class TaskListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.all().order_by("-created_at")
        serializer = TaskWithMembersSerializer(tasks, many=True)
        return Response({
            "success": True,
            "message": "Tasks retrieved successfully",
            "data": serializer.data
        })

# employee 

# tasks , projects count
class ProjectTaskCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_projects = Project.objects.count()
        total_tasks = Task.objects.count()

        return Response({
            "success": True,
            "message": "Counts retrieved successfully",
            "total_projects": total_projects,
            "total_tasks": total_tasks
        })


# single employee project and task details by employee id 
class EmployeeIdProjectsTasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        try:
            # Get employee detail by employee_id
            employee = EmployeeDetail.objects.get(id=employee_id)
            user = employee.user
        except EmployeeDetail.DoesNotExist:
            return Response({"status": "failed", "message": "Employee not found"}, status=404)

        # ------------------------
        # Projects for this employee
        # ------------------------
        projects = ProjectMembers.objects.filter(
            team_leader__contains=[user.id]
        ) | ProjectMembers.objects.filter(
            project_manager__contains=[user.id]
        ) | ProjectMembers.objects.filter(
            tags__contains=[user.id]
        )

        project_list = []
        for pm in projects:
            project_list.append({
                "project_id": pm.project.id,
                "project_name": pm.project.project_name,
                "client": pm.project.client,
                "start_date": pm.project.start_date,
                "end_date": pm.project.end_date,
                "priority": pm.project.priority,
                "status": pm.project.status,
            })

        # ------------------------
        # Tasks assigned to this employee
        # ------------------------
        tasks = Task.objects.filter(assigned_to=user)
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "project": task.project.project_name if task.project else None,
                "assigned_by": task.assigned_by.email if task.assigned_by else None,
                "assigned_to": task.assigned_to.email if task.assigned_to else None,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            })

        return Response({
            "status": "success",
            "employee_id": employee.employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "projects": project_list,
            "tasks": task_list
        })

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
class LeaveAcceptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        leave_id = request.data.get("leave_id")
        if not leave_id:
            return Response(
                {"success": False, "message": "leave_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave = get_object_or_404(Leave, id=leave_id)

        if leave.status != "Pending":
            return Response(
                {"success": False, "message": f"Leave already {leave.status.lower()}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave.status = "Approved"
        leave.approved_by = request.user
        leave.save()

        # Send notification to the employee who applied for leave
        if leave.user:
            NotificationLog.objects.create(
                user=leave.user,
                action=f"Your leave request for {leave.leave_type} from {leave.start_date} to {leave.end_date} has been approved by {request.user.email}",
                title = "Leave Approved"
            )

        return Response(
            {"success": True, "message": "Leave request approved successfully"},
            status=status.HTTP_200_OK,
        )


class LeaveRejectAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        leave_id = request.data.get("leave_id")
        rejection_reason = request.data.get("rejection_reason", None)

        if not leave_id:
            return Response(
                {"success": False, "message": "leave_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave = get_object_or_404(Leave, id=leave_id)

        if leave.status != "Pending":
            return Response(
                {"success": False, "message": f"Leave already {leave.status.lower()}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leave.status = "Rejected"
        leave.approved_by = request.user
        if rejection_reason:
            leave.rejection_reason = rejection_reason  
        leave.save()

        # Send notification to the employee who applied for leave
        if leave.user:
            notification_message = f"Your leave request for {leave.leave_type} from {leave.start_date} to {leave.end_date} has been rejected by {request.user.email}"
            if rejection_reason:
                notification_message += f". Reason: {rejection_reason}"
            
            NotificationLog.objects.create(
                user=leave.user,
                action=notification_message,
                title = "Leave Rejected"
            )

        return Response(
            {"success": True, "message": "Leave request rejected successfully"},
            status=status.HTTP_200_OK,
        )



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

        employees = EmployeeDetail.objects.filter(user__is_active=True)
        serializer = EmployeeDetailSerializer(employees, many=True)
        return Response(
            {
                'message': 'Employees listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )



#  list of some employee user_types
class TeamLeaderListAPIView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        team_leaders = EmployeeDetail.objects.filter(user_type="Teamleader", )
        serializer = FilterNameSerializer(team_leaders, many=True)
        return Response(
            {
                'message': 'Team leaders listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
        
        
class ProjectmanagerListAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        project_managers = EmployeeDetail.objects.filter(user_type="Project Manager")
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
        Employee = EmployeeDetail.objects.filter(user_type="Employee")
        serializer = EmployeeNameSerializer(Employee, many=True)
        return Response(
            {
                'message': 'Employee listed successfully',
                'employees': serializer.data
            },
            status=status.HTTP_200_OK
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



# total counts employes  attendance in the employee dashboard     
class AttendanceSummaryView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        # Get today's date
        today = now().date()
        last_7_days = today - timedelta(days=7)

        # Attendance summary (today only)
        total_employees = EmployeeDetail.objects.count()
        present_count = Attendance.objects.filter(date=today, status="Present").count()
        absent_count = Attendance.objects.filter(date=today, status="Absent").count()
        onlineemployee_count = EmployeeDetail.objects.filter( job_type="onlineemployee").count()
        onlineintern_count = EmployeeDetail.objects.filter( job_type="onlineintern").count()
        offlineemployee_count = EmployeeDetail.objects.filter( job_type="offlineemployee").count()
        offlineintern_count = EmployeeDetail.objects.filter( job_type="offlineintern").count()


        # Employee stats
        new_employees_today = EmployeeDetail.objects.filter(created_at__date=today).count()
        # new_employees_last_7_days = EmployeeDetail.objects.filter(created_at__date__gte=last_7_days).count()

        data = {
            "total_employees": total_employees,
            "active": present_count,
            "inactive": absent_count,
            "new_employees_today": new_employees_today,
            "onlineemployee_count": onlineemployee_count,
            "onlineintern_count": onlineintern_count,
            "offlineemployee_count": offlineemployee_count,
            "offlineintern_count": offlineintern_count,
            # "new_employees_last_7_days": new_employees_last_7_days,
        }

        response = {
            "status": True,
            "message": "Attendance summary fetched successfully",
            "data": data,
        }

        return Response(response)



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
      
        counts = (
            EmployeeDetail.objects
            .values('designation')
            .annotate(total=Count('id'))
            .order_by('designation')
        )

      
        result = [
            {
                "designation": item['designation'] if item['designation'] else "Not Specified",
                "count": item['total']
            }
            for item in counts
        ]

        return Response({
            "success": True,
            "message": "Employee counts by designation",
            "data": result
        })

# todays employee count by designation

class TodayEmployeeCountByDesignation(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        # ✅ Get unique employees who punched in today
        attendance_today = (
            Attendance.objects
            .filter(date=today, punch_in=True)
            .values("employee__designation", "employee")  # include employee for uniqueness
            .distinct()  # ensures unique employee per day
        )

        # ✅ Count unique employees per designation
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


# todays attendance count  all employees
class TodaysAttendanceCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        # Get each employee's first punch-in record for today
        first_punches = (
            Attendance.objects.filter(date=today)
            .values("employee")
            .annotate(first_in=Min("in_time"))
        )

        present_count = 0
        late_count = 0

        for record in first_punches:
            first_in = record["first_in"]
            if first_in:
                # Convert to local time if timezone-aware
                local_in_time = timezone.localtime(first_in)
                punch_time = local_in_time.time()

                # ✅ Compare correctly
                if punch_time <= time(9, 40):
                    present_count += 1
                else:
                    late_count += 1

        # Leave count (unique employees on leave today)
        leave_count = Leave.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status="Approved"
        ).values("employee").distinct().count()

        return Response({
            "success": True,
            "date": today,
            "present_count": present_count,
            "late_count": late_count,
            "leave_count": leave_count
        })

# ADMIN Filter employee designation wise list       
class EmployeeListAdminFilteredView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        today = date.today()
        designation = request.query_params.get("designation")
        

        employees = EmployeeDetail.objects.all()

        # ✅ Filtering
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


# all employees daily checkin checkout details
class AllTodaysEmployeeCheckinCheckOutDetails(APIView):
    permission_classes = [IsAuthenticated] 
    def get(self, request):
        today = date.today()

        # Aggregate per employee: earliest in, latest out
        qs = (
            Attendance.objects.filter(date=today)
            .values("employee_id", "employee__first_name")
            .annotate(
                first_in=Min("in_time"),
                last_out=Max("out_time")
            )
            .order_by("employee__first_name")
        )

        data = []
        cutoff_time = time(9, 40)  # 09:40 AM cutoff

        for record in qs:
            first_in = record["first_in"]
            last_out = record["last_out"]

            # -------------------
            # Late check
            # -------------------
            is_late = False
            late_duration = "00 h 00 m"

            if first_in:
                # Convert to local timezone
                first_in_local = first_in.astimezone()
                first_in_clock = first_in_local.time()

                # Calculate late duration in seconds
                delta_seconds = (
                    first_in_clock.hour * 3600 + first_in_clock.minute * 60 + first_in_clock.second
                    - cutoff_time.hour * 3600 - cutoff_time.minute * 60
                )

                if delta_seconds > 0:
                    is_late = True
                    hours, remainder = divmod(delta_seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    late_duration = f"{hours:02d} h {minutes:02d} m"
                else:
                    is_late = False
                    late_duration = "00 h 00 m"

            # -------------------
            # Production hours
            # -------------------
            production_hours = "00:00:00"
            if first_in and last_out:
                delta = last_out - first_in
                total_seconds = int(delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                production_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            data.append({
                "employee_id": record["employee_id"],
                "employee_name": record["employee__first_name"],
                "date": str(today),
                "in_time": first_in.astimezone().strftime("%H:%M:%S") if first_in else None,
                "out_time": last_out.astimezone().strftime("%H:%M:%S") if last_out else None,
                "late": is_late,
                "late_duration": late_duration,
                "production_hours": production_hours,
            })

        return Response({
            "success": True,
            "message": "Employee attendance details listed successfully",
            "date": str(today),
            "total_records": len(data),
            "data": data
        })


# empployee all attendance details by emp id 
class EmployeeAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_object_or_404(EmployeeDetail, id=employee_id)
        serializer = EmployeeAttendanceSerializer(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })
    

# filter employee attendance by status present , absent , late 
class EmployeeAttendanceFilterByStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        status = request.query_params.get("status")
        status = status.strip().title()

        if status not in ["Present", "Absent", "Late"]:
            return Response({
                "status": False,
                "message": "Invalid status. Must be 'Present', 'Absent', or 'Late'."
            }, status=400)

        # Get the employee
        employee = get_object_or_404(EmployeeDetail, id=employee_id)

        # Filter employee's attendance by status
        latest_status = (
            Attendance.objects.filter(employee=employee, date=OuterRef("date"))
            .order_by("-out_time")
            .values("status")[:1]
        )

        qs = (
            Attendance.objects.filter(employee=employee, status=status)
            .values("date")
            .annotate(
                in_time=Min("in_time"),
                out_time=Max("out_time"),
                status=Subquery(latest_status),
            )
            .order_by("-date")
        )

        # Serialize the grouped daily data
        daily_data = DailyAttendanceSerializer(qs, many=True).data

        # Include employee info
        employee_data = {
            "id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "profile_pic": employee.profile_pic.url if employee.profile_pic else None,
            "employee_id": employee.employee_id,
            "attendances": daily_data,
        }

        return Response({
            "status": True,
            "message": f"Attendance with status '{status}' fetched successfully",
            "data": employee_data,
        })

# past 7 days attendance details
class EmployeeAttendanceViewpast7days(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_object_or_404(EmployeeDetail, id=employee_id)
        serializer = EmployeeAttendanceSerializerpast7days(employee)
        return Response({
            "status": True,
            "data": serializer.data
        })

# list employee attendence details by date range
class AttendanceByDateRangeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_id = request.query_params.get("employee_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not employee_id or not start_date or not end_date:
            return Response({
                "status": False,
                "message": "employee_id, start_date, and end_date are required"
            }, status=400)

        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "status": False,
                "message": "Employee not found"
            }, status=404)

        attendances = Attendance.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        ).order_by("-date")

        serializer = AttendanceSerializer(attendances, many=True)
        return Response({
            "status": True,
            "message": f"Attendance records for {employee.first_name} from {start_date} to {end_date}",
            "data": serializer.data
        })



#employee attendence details edit by admin        
class AttendanceEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        attendance = get_object_or_404(Attendance, pk=pk)
        serializer = AttendanceEditSerializer(attendance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Attendance updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=400)
# api for temporary removing employee from the system
class RemoveEmployeeAPIView(APIView):
    """
    API to temporarily remove an employee from the system (soft delete) 
    with exit status and exit date.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to remove employees."},
                status=status.HTTP_403_FORBIDDEN
            )

        employee_id = request.data.get("employee_id")
        emp_status = request.data.get("emp_status")  # e.g., "Resignation", "Termination"

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
        employee.save()

    
        if employee.user:
            employee.user.is_active = False
            employee.user.save()

            # 🔒 Blacklist all their tokens
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
        user = request.user

        # Only admin/superadmin can reactivate
        if user.role not in ['admin', 'superadmin']:
            return Response(
                {"success": False, "message": "You are not authorized to reactivate employees."},
                status=status.HTTP_403_FORBIDDEN
            )

        employee_id = request.data.get("employee_id")
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
        serializer = EmployeeSerializer(inactive_employees, many=True)
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
        serializer = EmployeeSerializer(active_employees, many=True)
        return Response({
            "success": True,
            "message": "Active employees fetched successfully",
            "data": serializer.data
        })


# holiday adding api
class HolidayCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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



# create department api
class DepartmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Department created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# create designation api
class DesignationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DesignationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Designation created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) 



# list all departments
class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response({
            "success": True,
            "message": "Departments fetched successfully",
            "data": serializer.data
        })

# list all designations
class DesignationListView(APIView): 
    permission_classes =[IsAuthenticated]
    def get(self, request):
        designations = Designation.objects.all()
        serializer = DesignationSerializer(designations, many=True)
        return Response({
            "success": True,
            "message": "Designations fetched successfully",
            "data": serializer.data
        })


     
class NotificationLogByUserAPIView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')  # Get user_id from URL
        return NotificationLog.objects.filter(user_id=user_id).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })

# notification log edit api
class NotificationLogEditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        log = get_object_or_404(NotificationLog, pk=pk)
        serializer = NotificationSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Notification log updated successfully",
                "data": serializer.data
            })
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# employees today birthdays        
      
        
class TodayBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        employees = EmployeeDetail.objects.filter(
            dob__month=today.month,
            dob__day=today.day
        )

        if not employees.exists():
            return Response(
                {
                    "success": False,
                    "message": "No birthdays today."
                },
                status=status.HTTP_200_OK
            )

        serializer = EmployeebirthdaySerializer(employees, many=True)
        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
#employees tomarow birthday
class TomorrowBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tomorrow = date.today() + timedelta(days=1)
        employees = EmployeeDetail.objects.filter(
            dob__month=tomorrow.month, dob__day=tomorrow.day
        )

        if employees.exists():
            serializer = EmployeebirthdaySerializer(employees, many=True)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": "No birthdays tomorrow"
            }, status=status.HTTP_200_OK)



#employees upcoming birthday comming 7 month


class UpcomingBirthdayAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = date.today()
        six_months_later = today + timedelta(days=183)  # approx 6 months

        # Extract month/day for filtering
        today_month, today_day = today.month, today.day
        end_month, end_day = six_months_later.month, six_months_later.day

        if today_month <= end_month:
            # Case 1: Both in same year range
            employees = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month, dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )
        else:
            # Case 2: Range spans year-end (e.g. Oct → Mar)
            employees = EmployeeDetail.objects.filter(
                Q(dob__month__gt=today_month) |
                Q(dob__month__lt=end_month) |
                Q(dob__month=today_month, dob__day__gte=today_day) |
                Q(dob__month=end_month, dob__day__lte=end_day)
            )

        if not employees.exists():
            return Response(
                {"success": False, "message": "No birthdays in the next 6 months."},
                status=status.HTTP_200_OK
            )

        serializer = EmployeebirthdaySerializer(employees, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )
    

# birthday wishes
class TodayBirthdaywishAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_today_birthdays(self):
        today = date.today()
        return EmployeeDetail.objects.filter(
            dob__month=today.month, dob__day=today.day
        )

    def post(self, request):
        """POST API: Send wishes + log them"""
        employees = self.get_today_birthdays()
        if not employees.exists():
            return Response({
                "success": False,
                "message": "No birthdays today to send wishes"
            }, status=status.HTTP_200_OK)

        # ✅ Individual wishes
        for emp in employees:
            wish_message = f"Happy Birthday {emp.first_name}! 🎉"
            title = "Birthday Wish"
            NotificationLog.objects.create(
                user=emp.user,      # ✅ save employee's user, not request.user
                action=wish_message,
                title=title
            )

        

        return Response({
            "success": True,
            "message": "Birthday wishes sent & logged successfully"
        }, status=status.HTTP_201_CREATED)


#birthday wish id wise       
class TodayBirthdayWishidAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        POST API: Send wish to a specific employee by ID.
        URL: /api/birthday-wish/<pk>/
        """
        try:
            emp = EmployeeDetail.objects.get(pk=pk)
        except EmployeeDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": f"Employee with id {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        if emp.dob.month != today.month or emp.dob.day != today.day:
            return Response({
                "success": False,
                "message": f"Today is not {emp.first_name}'s birthday"
            }, status=status.HTTP_400_BAD_REQUEST)

        wish_message = (
            f"Happy Birthday {emp.first_name}! 🎉 "
           # f"May your day be filled with laughter, love, and wonderful moments!"
        )

        NotificationLog.objects.create(
            user=emp.user,
            action=wish_message,
            title = "Birthday Wish"
        )

        return Response({
            "success": True,
            "message": "Birthday wish sent & logged successfully",
            "wish": {
                "employee_id": emp.pk,
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "wish": wish_message,
                "profile_url": f"/employees/{emp.pk}/"
            }
        }, status=status.HTTP_201_CREATED)
    

# list all notifications of the login user
class AdminNotificationLogListAPIView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(user=self.request.user).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })
    

# total project and task  count overview
class ProjectCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()

        total_projects = Project.objects.count()
        pending_count = Project.objects.filter(status__iexact="Pending").count()
        on_going_count = Project.objects.filter(status__iexact="on going").count()
        completed_count = Project.objects.filter(status__iexact="Completed").count()
        on_hold_count = Project.objects.filter(status__iexact="On Hold").count()

        # Overdue = End date < today and not completed
        overdue_count = Project.objects.filter(
            end_date__lt=today
        ).exclude(status__iexact="Completed").count()

        return Response({
            "success": True,
            "total_projects": total_projects,
            "pending_projects": pending_count,
            "on_going_projects":  on_going_count,
            "completed_projects": completed_count,
            "on_hold_projects": on_hold_count,
            "overdue_projects": overdue_count,
        })
        
        
        
        
        
class TaskCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()

        total_task = Task.objects.count()
        pending_task_count = Task.objects.filter(status__iexact="Pending").count()
        on_going_task_count = Task.objects.filter(status__iexact="on going").count()
        completed_task_count = Task.objects.filter(status__iexact="Completed").count()
        on_hold_task_count = Task.objects.filter(status__iexact="On Hold").count()
        overdue_task_count = Task.objects.filter(status__iexact="Overdue").count()

      

        return Response({
              "success": True,
            "total_tasks": total_task,
            "pending_tasks": pending_task_count,
            "on_going_tasks": on_going_task_count,
            "completed_tasks": completed_task_count,
            "on_hold_tasks": on_hold_task_count,
            "overdue_task_count":overdue_task_count
           
        })    
    

class Last7DaysTasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Calculate 7 days ago
        seven_days_ago = timezone.now() - timedelta(days=7)

        # Filter tasks created in the last 7 days and order by created_at descending
        tasks = Task.objects.filter(created_at__gte=seven_days_ago).order_by("-created_at")
        
        serializer = TaskWithMembersSerializer(tasks, many=True)
        return Response({
            "success": True,
            "message": "Tasks from the last 7 days retrieved successfully",
            "data": serializer.data
        })    
    

# filter tasks by status from url
class TaskStatusFilterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_tasks_by_status(self, status_filter):
        """
        Helper function to get tasks filtered by status.
        """
        if status_filter:
            return Task.objects.filter(status__iexact=status_filter).order_by("-created_at")
        return Task.objects.none()  # return empty queryset if no filter provided

    def get(self, request, status_filter):
        """
        Fetch tasks filtered by status from URL.
        Example: /api/taskliststatusfilter/status=Pending/
        """
        # Clean URL parameter like "status=Pending"
        if status_filter.startswith("status="):
            status_value = status_filter.split("=", 1)[1]
        else:
            status_value = status_filter

        tasks = self.get_tasks_by_status(status_value)
        serializer = TaskWithMembersSerializer(tasks, many=True)

        return Response({
            "success": True,
            "message": f"Tasks with status '{status_value}' retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

# branch creation listing api 

class BranchCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Branch created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        branches = Branch.objects.all()
        serializer = BranchSerializer(branches, many=True)
        return Response({
            "success": True,
            "message": "Branches fetched successfully",
            "data": serializer.data
        })    
    

# recent activities
class EmployeeActivityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        # --- Latest leave record for each employee applied today ---
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
            employee_activities.append({
                "type": "Task",
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "project_name": task.project.project_name if task.project else None,
                "assigned_by": task.assigned_by.first_name if task.assigned_by else None,
                "assigned_to": task.assigned_to.first_name if task.assigned_to else None,
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
            activities.append({
                "type": "Task",
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "project_name": task.project.project_name if task.project else None,
                "assigned_by": task.assigned_by.first_name if task.assigned_by else None,
                "assigned_to": task.assigned_to.first_name if task.assigned_to else None,
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