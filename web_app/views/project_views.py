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



# todays task pecentage want to update later based on employee updations
class TaskPercentageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()

        # Filter today's tasks (you can also add employee filter if needed)
        tasks_today = Task.objects.filter(updated_at__date=today)  # or created_at__date=today
        total_task = tasks_today.count()

        if total_task == 0:
            return Response({
                "success": True,
                "message": "No tasks updated today",
                "data": {
                    "pending": 0,
                    "on_going": 0,
                    "completed": 0,
                    "on_hold": 0,
                    "overdue": 0,
                }
            })

        # Count each status for today
        pending_count = tasks_today.filter(status__iexact="Pending").count()
        on_going_count = tasks_today.filter(status__iexact="On Going").count()
        completed_count = tasks_today.filter(status__iexact="Completed").count()
        on_hold_count = tasks_today.filter(status__iexact="On Hold").count()
        overdue_count = tasks_today.filter(status__iexact="Overdue").count()

        def percent(count):
            return int(round((count / total_task) * 100))

        return Response({
            "success": True,
            "message": "Today's task percentage",
            "total_tasks_today": total_task,
            "data": {
                "pending": percent(pending_count),
                "on_going": percent(on_going_count),
                "completed": percent(completed_count),
                "on_hold": percent(on_hold_count),
                "overdue": percent(overdue_count),
            }
        })

# todays total  tasks hous
class TodaysTaskHoursAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        now = timezone.now()

        # Get all tasks updated today (all employees)
        tasks_today = Task.objects.filter(updated_at__date=today)

        total_hours = timedelta()

        task_data = []
        for t in tasks_today:
            # Calculate difference between now and updated_at
            hours_spent = (now - t.updated_at).total_seconds() / 3600
            hours_spent = round(hours_spent, 2)

            total_hours += timedelta(hours=hours_spent)

            task_data.append({
                # "task_id": t.id,
                # "task_name": getattr(t, 'name', ''),
                # "employee": getattr(t.assigned_to, 'name', '') if hasattr(t, 'assigned_to') else None,
                # "last_updated": t.updated_at,
                 "hours_spent": f"{hours_spent} / 8 hrs"
            })

        total_hours_in_hours = round(total_hours.total_seconds() / 3600, 2)

        return Response({
            "success": True,
            "message": "Total hours (based on current time vs last update)",
            "total_hours": total_hours_in_hours,
            "data": task_data
        })
    
# add project api 

class AddProjectApi(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
        print(request.data)
        data = {}
        for key in request.data.keys():
            data[key] = request.data.get(key)

        # Parse JSON fields (members and tasks)
        for field in ["members", "tasks"]:
            raw_value = data.get(field)
            if isinstance(raw_value, str) and raw_value:
                try:
                    data[field] = json.loads(raw_value)
                except json.JSONDecodeError:
                    return Response({field: ["Invalid JSON."]}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(data.get("members"), dict):
            data["members"] = [data["members"]]
        if isinstance(data.get("tasks"), dict):
            data["tasks"] = [data["tasks"]]

        serializer = ProjectSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            project = serializer.save(assigned_by=request.user)

            # Create notifications for all assigned employees per task
            for task_data in data.get("tasks", []):
                assigned_to_ids = task_data.get("assigned_to", [])
                for user_id in assigned_to_ids:
                    try:
                        assigned_user = User.objects.get(id=user_id)
                        NotificationLog.objects.create(
                            user=assigned_user,
                            title="New Task Assigned",
                            action=f"You have been assigned to the task '{task_data.get('title')}' in project '{project.project_name}'."
                        )
                    except User.DoesNotExist:
                        continue

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
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
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
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
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
    def create(self, request, *args, **kwargs):
        print("🔹 Request Data:", request.data)   # 👈 This will print in your terminal
        return super().create(request, *args, **kwargs)
    
    
    
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

        project_id = request.data.get("project_id")
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
        # print(request.data) 
        # decrypted_data = decrypt_request_payload(request)

        # if decrypted_data:
        #         print("Decrypted Request:", decrypted_data)
        #         # Replace request.data with decrypted version
        #         data = decrypted_data
        # else:
        #         print("Normal  Request:", request.data)
        #         data = request.data
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
        serializer = ListTaskWithMembersSerializer(tasks, many=True)
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

    def _to_datetime(self, dt):
        """Ensure timezone-naive datetime conversion."""
        if dt is None:
            return None
        if is_aware(dt):
            dt = make_naive(dt)
        return dt

    def get(self, request, employee_id):
        try:
            employee = EmployeeDetail.objects.get(id=employee_id)
            user = employee.user
        except EmployeeDetail.DoesNotExist:
            return Response({"status": "failed", "message": "Employee not found"}, status=404)

        # --- Projects where the employee is involved ---
        project_members = ProjectMembers.objects.filter(
            Q(team_leader__contains=[user.id]) |
            Q(project_manager__contains=[user.id]) |
            Q(tags__contains=[user.id])
        )

        # --- Also include projects linked via tasks ---
        task_projects = Project.objects.filter(task__assigned_to=user).distinct()

        all_projects = Project.objects.filter(
            Q(id__in=project_members.values_list('project_id', flat=True)) |
            Q(id__in=task_projects.values_list('id', flat=True))
        ).distinct()

        project_list = []

        for project in all_projects:
            project_tasks = Task.objects.filter(project=project)
            total_project_tasks = project_tasks.count()

            employee_tasks = project_tasks.filter(assigned_to=user)

            # --- Task counts ---
            employee_task_count = employee_tasks.count()

            # --- Total working hours from all employee tasks (sum of field) ---
            total_hours = 0.0
            for t in employee_tasks:
                if t.total_working_hours:
                    try:
                        total_hours += float(t.total_working_hours)
                    except ValueError:
                        pass

            # --- Time spent (sum of created→updated diffs) ---
            total_time_spent = 0.0
            for t in employee_tasks:
                if t.created_at and t.updated_at:
                    start = self._to_datetime(t.created_at)
                    end = self._to_datetime(t.updated_at)
                    total_time_spent += (end - start).total_seconds() / 3600  # in hours

            # --- Task list ---
            task_list = []
            for task in employee_tasks:
                assigned_to_users = task.assigned_to.all()
                assigned_to_list = []
                for u in assigned_to_users:
                    try:
                        emp_detail = EmployeeDetail.objects.get(user=u)
                        profile_pic_url = (
                            request.build_absolute_uri(emp_detail.profile_pic.url)
                            if emp_detail.profile_pic else None
                        )
                        assigned_to_list.append({
                            "id": emp_detail.id,
                            "name": f"{emp_detail.first_name} {emp_detail.last_name}",
                            "email": u.email,
                            "profile_pic": profile_pic_url
                        })
                    except EmployeeDetail.DoesNotExist:
                        assigned_to_list.append({
                            "id": u.id,
                            "name": f"{u.first_name} {u.last_name}",
                            "email": u.email,
                            "profile_pic": None
                        })
                # Individual task time spent
                time_spent = None
                if task.created_at and task.updated_at:
                    start = self._to_datetime(task.created_at)
                    end = self._to_datetime(task.updated_at)
                    time_spent = round((end - start).total_seconds() / 3600, 2)

                task_list.append({
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_by": f"{task.assigned_by.first_name} {task.assigned_by.last_name}" if task.assigned_by else None,
                    "assigned_to": assigned_to_list,
                    "time_spent_hours": time_spent,
                    "total_working_hours": task.total_working_hours,
                    "created_at": task.created_at,
                    "due_date": task.due_date,
                    "updated_at": task.updated_at,
                })

            # --- Add project with summary ---
            project_list.append({
                "project_id": project.id,
                "project_logo": request.build_absolute_uri(project.project_logo.url) if project.project_logo else None,
                "project_name": project.project_name,
                "client": project.client,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "priority": project.priority,
                "project_value": project.project_value,
                "status": project.status,
                "description": project.description,
                "task_summary": f"{employee_task_count} / {total_project_tasks} tasks",
                "time_summary": f"{round(total_time_spent, 2)} / {round(total_hours, 2)} hrs",
                "tasks": task_list,
            })

        # --- Tasks without project ---
        unassigned_tasks = Task.objects.filter(project__isnull=True, assigned_to=user)
        other_task_list = []
        for t in unassigned_tasks:
            time_spent = None
            if t.created_at and t.updated_at:
                start = self._to_datetime(t.created_at)
                end = self._to_datetime(t.updated_at)
                time_spent = round((end - start).total_seconds() / 3600, 2)

            other_task_list.append({
                "task_id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "assigned_by": t.assigned_by.email if t.assigned_by else None,
                "assigned_to": [u.email for u in t.assigned_to.all()],
                "time_spent_hours": time_spent,
                "total_working_hours": t.total_working_hours,
                "created_at": t.created_at,
                "due_date": t.due_date,
                "updated_at": t.updated_at,
            })

        profile_pic_url = request.build_absolute_uri(employee.profile_pic.url) if employee.profile_pic else None

        return Response({
            "status": "success",
            "id": employee.id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "profile_pic_url": profile_pic_url,
            "projects": project_list,
            "unassigned_tasks": other_task_list
        }, status=200)


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
    
    



class ProjectManagerSearchView(APIView):
    """
    Get Project Managers filtered by letters or text in the query param.
    Example: /api/project-managers/?letter=ra
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_text = request.query_params.get("letter", "").strip().lower()

        # ❌ DO NOT FILTER encrypted fields in ORM
        # Just reduce dataset safely (active users only)
        employees = EmployeeDetail.objects.filter(user__is_active=True)

        filtered_managers = []

        for emp in employees:
            # 🔓 Decrypt fields safely
            designation = decrypt_value(emp.designation) if emp.designation else ""
            user_type = decrypt_value(emp.user_type) if emp.user_type else ""
            reporting_manager = decrypt_value(emp.reporting_manager) if emp.reporting_manager else ""

            first_name = decrypt_value(emp.first_name) if emp.first_name else ""
            last_name = decrypt_value(emp.last_name) if emp.last_name else ""

            # ✅ Project Manager condition (after decrypt)
            is_pm = (
                designation.lower() == "project manager"
                or user_type.lower() == "project manager"
                or reporting_manager.lower() in ["mgr1", "mgr2"]
            )

            if not is_pm:
                continue

            # 🔍 Name search condition
            if search_text:
                if (
                    search_text not in first_name.lower()
                    and search_text not in last_name.lower()
                ):
                    continue

            # Attach decrypted names for serializer
            emp.first_name = first_name
            emp.last_name = last_name

            filtered_managers.append(emp)

        # 🔠 Sort alphabetically by decrypted first name
        filtered_managers.sort(key=lambda x: x.first_name.lower())

        serializer = ProjectManagerSearchListSerializer(filtered_managers, many=True)

        return Response(
            {
                "success": True,
                "message": "Project managers listed successfully",
                "count": len(filtered_managers),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )


# team leader search
class TeamLeaderSearchListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to list team leaders filtered by first or last name starting with a given letter.
        Supports:
            /api/team-leaders-search/A/
            /api/team-leaders-search/?letter=A
        """

        # Get the search letter
        letter = kwargs.get("letter") or request.GET.get("letter", "")
        letter = letter.strip().lower()

        # ❌ DO NOT filter encrypted fields here
        # Only reduce dataset safely
        employees = EmployeeDetail.objects.filter(
            user__is_active=True
        ).select_related("user")

        filtered = []

        for emp in employees:
            # 🔓 Decrypt safely
            designation = decrypt_value(emp.designation) if emp.designation else ""
            user_type = decrypt_value(emp.user_type) if emp.user_type else ""
            reporting_manager = decrypt_value(emp.reporting_manager) if emp.reporting_manager else ""

            first_name = decrypt_value(emp.first_name) if emp.first_name else ""
            last_name = decrypt_value(emp.last_name) if emp.last_name else ""

            # ✅ Team Leader condition (after decryption)
            is_team_leader = (
                emp.is_team_lead is True or
                designation.lower() == "team leader" or
                user_type.lower() == "team leader" or
                reporting_manager.lower() in ["team leader 1", "team leader 2"]
            )

            if not is_team_leader:
                continue

            # 🔍 Name starts-with filter
            if letter:
                if (
                    not first_name.lower().startswith(letter)
                    and not last_name.lower().startswith(letter)
                ):
                    continue

            # Attach decrypted values for serializer
            emp.decrypted_first_name = first_name
            emp.decrypted_last_name = last_name

            filtered.append(emp)

        # 🔠 Sort by decrypted first name
        filtered.sort(key=lambda x: x.decrypted_first_name.lower())

        serializer = TeamLeaderSearchSerializer(
            filtered, many=True, context={"request": request}
        )

        return Response(
            {
                "message": "Team Leader list fetched successfully",
                "count": len(filtered),
                "team_leaders": serializer.data,
            },
            status=status.HTTP_200_OK
        )
# employee search by name 
class EmployeeRoleSearchByNameAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        letter = kwargs.get("letter") or request.GET.get("letter")
        letter = (letter or "").strip().lower()

        # Base queryset: all employees
        queryset = EmployeeDetail.objects.filter(user__role__iexact="employee")

        # Decrypt + filter manually
        filtered_employees = []
        for emp in queryset:
            first_name = decrypt_value(emp.first_name) if emp.first_name else ""
            last_name = decrypt_value(emp.last_name) if emp.last_name else ""

            # Match the first letter (case-insensitive)
            if not letter or first_name.lower().startswith(letter) or last_name.lower().startswith(letter):
                emp.first_name = first_name
                emp.last_name = last_name
                filtered_employees.append(emp)

        # Sort alphabetically by decrypted first name
        filtered_employees.sort(key=lambda e: e.first_name.lower())

        serializer = EmployeeSearchSerializer(filtered_employees, many=True)
        return Response({
            "message": "Employee list fetched successfully",
            "count": len(filtered_employees),
            "employees": serializer.data
        }, status=status.HTTP_200_OK)


class CeocmoSearchListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to list CEO, CTO, CMO, or CHO employees,
        optionally filtered by first or last name starting with a given letter.

        Examples:
            /api/ceocmo-search/A/
            /api/ceocmo-search/?letter=A
        """

        # Get search letter
        letter = kwargs.get("letter") or request.GET.get("letter", "")
        letter = letter.strip().lower()

        # ❌ Do NOT filter encrypted fields in ORM
        employees = EmployeeDetail.objects.filter(
            user__is_active=True
        ).select_related("user")

        filtered = []

        for emp in employees:
       
            designation = decrypt_value(emp.designation) if emp.designation else ""
            user_type = decrypt_value(emp.user_type) if emp.user_type else ""

            first_name = decrypt_value(emp.first_name) if emp.first_name else ""
            last_name = decrypt_value(emp.last_name) if emp.last_name else ""

           
            is_c_level = designation.lower() in ["ceo", "cto", "cmo", "cho"] or \
                         user_type.lower() in ["ceo", "cto", "cmo", "cho"]

            if not is_c_level:
                continue

         
            if letter:
                if (
                    not first_name.lower().startswith(letter)
                    and not last_name.lower().startswith(letter)
                ):
                    continue

            # Attach decrypted values for serializer
            emp.decrypted_first_name = first_name
            emp.decrypted_last_name = last_name

            filtered.append(emp)

        filtered.sort(key=lambda x: x.decrypted_first_name.lower())

        serializer = CeoctoSearchSerializer(filtered, many=True)

        return Response({
            "success": True,
            "message": "C-level employees fetched successfully",
            "count": len(filtered),
            "executives": serializer.data
        }, status=status.HTTP_200_OK)
    



# list all project new api after adding all required fields
class NewListProjectsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
      
        projects = Project.objects.all().order_by("-created_at")

       
        decrypted_projects = []
        for project in projects:
            decrypted_status = decrypt_value(project.status)
            if decrypted_status.lower() == "pending":
                project.status = decrypted_status  
                decrypted_projects.append(project)

        serializer = NewProjectReadSerializer(decrypted_projects, many=True,context={'request': request})
        return Response({
            "success": True,
            "message": "Projects listed successfully",
            "projects": serializer.data
        }, status=status.HTTP_200_OK)    
    
