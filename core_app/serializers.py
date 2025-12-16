from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from . models import *
from datetime import datetime
from django.utils.timezone import make_naive
from django.utils.timezone import now, make_naive,is_aware
from datetime import datetime, time



# -----------------------------
# User Login Serializer
# -----------------------------
class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
        }


# -----------------------------
# Bank Detail Serializer
# -----------------------------
class BankDetailSerializer(serializers.ModelSerializer):
    accountNumber = serializers.CharField(source="account_number")
    ifscCode = serializers.CharField(source="ifsc_code")
    branchName = serializers.CharField(source="branch_name")
    accountHolder = serializers.CharField(source="account_holder")

    class Meta:
        model = BankDetail
        fields = [
            "id", "accountNumber", "bank_name","ifscCode", "branchName",
            "accountHolder", "documents", "created_at", "updated_at"
        ]


# -----------------------------
# Employee Serializer
# -----------------------------
class EmployeeSerializer(serializers.ModelSerializer):
    # CamelCase mapping
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    employeeId = serializers.CharField(source="employee_id")

    # Manager now stored as plain text
    repMgrTl = serializers.CharField(
        source="reporting_manager",
        required=False,
        allow_blank=True,
        allow_null=True
    )

    confirmPassword = serializers.CharField(write_only=True, required=True)

    # Email & password for linked User
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    # Bank fields
    accountNumber = serializers.CharField(write_only=True, required=False)
    bank_name = serializers.CharField(write_only=True, required=False)
    confirmAccountNumber = serializers.CharField(write_only=True, required=False)
    ifscCode = serializers.CharField(write_only=True, required=False)
    branchName = serializers.CharField(write_only=True, required=False)
    accountHolderName = serializers.CharField(write_only=True, required=False)
    documents = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )


    # Profile picture
    profile_pic = serializers.ImageField(required=False)
    employee_shift = serializers.PrimaryKeyRelatedField(
    queryset=ShiftTable.objects.all(),
    required=False,
    allow_null=True)
    basic_earnings = serializers.CharField(write_only=True, required=False)
    pf_deduction = serializers.CharField(write_only=True, required=False)
    employee_state_insurance = serializers.CharField(write_only=True, required=False)
    income_tax = serializers.CharField(write_only=True, required=False)
    proffessional_tax = serializers.CharField(write_only=True, required=False)
    



    class Meta:
        model = EmployeeDetail
        fields = [
            "id", "firstName", "lastName", "employeeId",
            "department", "designation", "repMgrTl", "is_team_lead",
            "salary", "email", "password", "confirmPassword",
            "profile_pic", "phone", "address", "dob","user_type","job_type",
            "gender", "nationality", "blood_group", "emergency_contact",
            # Bank fields
            "accountNumber","bank_name","confirmAccountNumber", "ifscCode",
            "branchName", "accountHolderName", "documents","company_branch","employee_shift","basic_earnings","pf_deduction","employee_state_insurance","income_tax","proffessional_tax",
        ]

    def validate(self, data):
        if data["password"] != data["confirmPassword"]:
            raise serializers.ValidationError("Passwords do not match")
        if data.get("accountNumber") and data.get("accountNumber") != data.get("confirmAccountNumber"):
            raise serializers.ValidationError("Account numbers do not match")
        validate_email(data["email"])
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        logged_in_user = request.user if request else None

        validated_data.pop("confirmPassword", None)
        raw_password = validated_data.pop("password")
        email = validated_data.pop("email")

        account_number = validated_data.pop("accountNumber", None)
        validated_data.pop("confirmAccountNumber", None)
        ifsc_code = validated_data.pop("ifscCode", None)
        branch_name = validated_data.pop("branchName", None)
        bank_name = validated_data.pop("bank_name", None)
        account_holder = validated_data.pop("accountHolderName", None)
        documents_files = validated_data.pop("documents", [])
        profile_pic_file = validated_data.pop("profile_pic", None)
        shift = validated_data.pop("employee_shift", None)
        if shift:
            validated_data["employee_shift"] = shift


        if profile_pic_file:
            validated_data["profile_pic"] = profile_pic_file

        # ---------------------------------
        # Determine role based on conditions
        # ---------------------------------
        user_type = validated_data.get("user_type", "").strip().lower()

        if logged_in_user and logged_in_user.role == "superadmin":
            user_role = "admin"  # ✅ Superadmin creates admins
            # Assign company_branch from data if provided
            company_branch = validated_data.get("company_branch")
            validated_data["company_branch"] = company_branch
        elif user_type in ["admin management", "admin team lead", "team lead", "team leader"]:
            user_role = "admin"
        else:
            user_role = "employee"

        # Create linked User
        user = User.objects.create(
            email=email,
            role=user_role,
            password=make_password(raw_password),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )

        # Create EmployeeDetail
        employee = EmployeeDetail.objects.create(user=user, **validated_data)
        if shift:
          employee.employee_shift = shift
          employee.save()

        # Create BankDetail if provided
        if account_number:
            bank_detail = BankDetail.objects.create(
                employee=employee,
                account_number=account_number,
                ifsc_code=ifsc_code,
                branch_name=branch_name,
                bank_name=bank_name,
                account_holder=account_holder,
            )
            for doc in documents_files:
                bank_detail.documents.save(doc.name, doc, save=True)

        return employee


class EmployeeDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "department",   
            "designation",
            "reporting_manager",
            "is_team_lead",
            "salary",
            "profile_pic",
            "phone",
            "address",
            "dob",
            "gender",
            "nationality",
            "blood_group",
            "emergency_contact",
            "created_at",
            "updated_at",
        ]

# attendance serializer
class AttendanceSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    in_time = serializers.SerializerMethodField()
    out_time = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "date",
            "in_time",
            "out_time",
            "attendance_type",
            "location",
            "latitude",       
            "longitude", 
            "qr_scan",
            "in_selfie",
            "out_selfie",
            "status",
            "verified_by",
            "created_at",
            "updated_at",
            "punch_in",
        ]

    def get_latitude(self, obj):
        if obj.qrsession:
            return obj.qrsession.latitudes
        return None

    def get_longitude(self, obj):
        if obj.qrsession:
            return obj.qrsession.longitude
        return None

    def get_in_time(self, obj):
        if obj.in_time:
            # Format: "YYYY-MM-DD HH:MM:SS"
            return obj.in_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None

    def get_out_time(self, obj):
        if obj.out_time:
            return obj.out_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None


#  leave serializer
class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_days = serializers.SerializerMethodField()
    employee_profile_pic = serializers.ImageField(source='employee.profile_pic', read_only=True)
    employee_designation = serializers.CharField(source='employee.designation', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    employee_job_type = serializers.SerializerMethodField()
    class Meta:
        model = Leave
        fields = [
            "id",
            "user",
            "employee_name",
            "employee_profile_pic",
            "employee_designation",
            "employee_department",
            "employee_job_type",
            "requested_date",
            "leave_days",
            "leave_type",
            "start_date",
            "end_date",
            "status",
            "approved_by",
            "attachments",
            "reason",
        ]
    def get_employee_name(self, obj):
        """Return employee's full name"""
        if obj.employee:
            first = obj.employee.first_name or ""
            last = obj.employee.last_name or ""
            full_name = f"{first} {last}".strip()
            return full_name
        return ""
    def get_leave_days(self, obj):
        """
        Calculate the number of days between start_date and end_date (inclusive)
        """
        if obj.start_date and obj.end_date:
            delta = obj.end_date - obj.start_date
            return delta.days + 1  # +1 to include both start and end date
        return 0    
    def get_employee_job_type(self, obj):
        """Return short form of job type"""
        if obj.employee and obj.employee.job_type:
            job_type = obj.employee.job_type.lower()
            if job_type == "work from office":
                return "WFO"
            elif job_type == "work from home":
                return "WFH"
            else:
                return obj.employee.job_type  # return as-is if something else
        return ""


# project , task , members  serializer
class TaskSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "assigned_by",
            "assigned_to",
            "status",
            "due_date",
            "priority",
            "attachments",
            "total_working_hours",
            "extra_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]



class TaskReadSerializer(serializers.ModelSerializer):
    assigned_by_id = serializers.IntegerField(source="assigned_by.id", read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    assigned_to_id = serializers.IntegerField(source="assigned_to.id", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    task_hours = serializers.SerializerMethodField()           # total hours
    current_progress = serializers.SerializerMethodField()     # current spent / total hours

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "assigned_by_id",
            "assigned_by_name",
            "assigned_to_id",
            "assigned_to_name",
            "created_at",
            "updated_at",
            "due_date",
            "task_hours",
            "current_progress",
        ]

    def get_assigned_by_name(self, obj):
    # assigned_by is a single User (ForeignKey)
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip()
        return None


    def get_assigned_to_name(self, obj):
        # assigned_to is a ManyToManyField
        return [
            f"{user.first_name} {user.last_name}".strip()
            for user in obj.assigned_to.all()
        ]




    def _normalize_datetime(self, value, end_of_day=False):
        """Convert date → datetime if needed, handle timezone-naive."""
        if isinstance(value, datetime):
            return make_naive(value) if is_aware(value) else value
        # if it's a date, convert to datetime (start or end of day)
        return datetime.combine(value, time(23, 59, 59) if end_of_day else time(0, 0, 0))

    def get_task_hours(self, obj):
        """Total available hours between created_at and due_date."""
        if obj.created_at and obj.due_date:
            start = self._normalize_datetime(obj.created_at)
            end = self._normalize_datetime(obj.due_date, end_of_day=True)
            delta = end - start
            return round(delta.total_seconds() / 3600, 2)
        return None

    def get_current_progress(self, obj):
        """Fraction value of hours spent so far / total hours."""
        if obj.created_at and obj.due_date:
            start = self._normalize_datetime(obj.created_at)
            end = self._normalize_datetime(obj.due_date, end_of_day=True)

            total_seconds = (end - start).total_seconds()
            elapsed_seconds = (self._normalize_datetime(now()) - start).total_seconds()

            if total_seconds <= 0:
                return "0 / 0 hours (0%)"

            progress_fraction = elapsed_seconds / total_seconds
            progress_fraction = max(0.0, min(progress_fraction, 1.0))

            total_hours = round(total_seconds / 3600, 2)
            current_hours = round(elapsed_seconds / 3600, 2)
            return f"{current_hours} / {total_hours} hours ({round(progress_fraction*100, 1)}%)"
        return None

class TaskWithProjectSerializer(serializers.ModelSerializer):
    assigned_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    project_details = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "assigned_by_name",
            "assigned_to_name",
            "created_at",
            "updated_at",
            "project_details",
        ]

    def get_assigned_by_name(self, obj):
        if obj.assigned_by and obj.assigned_by.employee_profile:
            return f"{obj.assigned_by.employee_profile.first_name} {obj.assigned_by.employee_profile.last_name}"
        return obj.assigned_by.email if obj.assigned_by else None

    def get_assigned_to_name(self, obj):
        if obj.assigned_to and obj.assigned_to.employee_profile:
            return f"{obj.assigned_to.employee_profile.first_name} {obj.assigned_to.employee_profile.last_name}"
        return obj.assigned_to.email if obj.assigned_to else None

    def get_project_details(self, obj):
        if obj.project:
            return {
                "id": obj.project.id,
                "project_name": obj.project.project_name,
                "client": obj.project.client,
                "start_date": obj.project.start_date,
                "end_date": obj.project.end_date,
                "priority": obj.project.priority,
                "project_value": obj.project.project_value,
                "total_working_hours": obj.project.total_working_hours,
                "extra_time": obj.project.extra_time,
                "description": obj.project.description,
                "status": obj.project.status,
                "project_logo": obj.project.project_logo.url if obj.project.project_logo else None,
                "attachment": obj.project.attachment.url if obj.project.attachment else None,
            }
        return None

class ProjectMembersSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = ProjectMembers
        fields = ["id","team_leader", "project_manager", "tags"]

class ProjectMembersReadSerializer(serializers.ModelSerializer):
    team_leader = serializers.SerializerMethodField()
    project_manager = serializers.SerializerMethodField()
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = ProjectMembers
        fields = ["id", "team_leader", "project_manager", "tags"]

    def get_team_leader(self, obj):
        data = obj.team_leader
        if not data:
            return None

        user_id = data.get("id")
        if not user_id:
            return data

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            # Assuming profile pic is stored in EmployeeDetail
            profile_pic = getattr(user.employee_profile, "profile_pic", None)
            pic_url = profile_pic.url if profile_pic else None
            return {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "profile_pic": pic_url
            }
        except User.DoesNotExist:
            return data

    def get_project_manager(self, obj):
        data = obj.project_manager
        if not data:
            return None

        user_id = data.get("id")
        if not user_id:
            return data

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            profile_pic = getattr(user.employee_profile, "profile_pic", None)
            pic_url = profile_pic.url if profile_pic else None
            return {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "profile_pic": pic_url
            }
        except User.DoesNotExist:
            return data


        

class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMembersSerializer(write_only=True, many=True)
    tasks = TaskSerializer(many=True, write_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "project_logo",
            "project_name",
            "client",
            "start_date",
            "end_date",
            "priority",
            "project_value",
            "total_working_hours",
            "extra_time",
            "description",
            "attachment",
            "members",
            "tasks",
        ]

    def create(self, validated_data):
        members_data = validated_data.pop("members", [])
        tasks_data = validated_data.pop("tasks", [])

        # Create Project
        project = Project.objects.create(**validated_data)

        # Create Project Members
        for member in members_data:
            ProjectMembers.objects.create(project=project, **member)

        # Create Tasks
        request = self.context.get("request")
        assigned_by_user = getattr(request, "user", None) if request else None

        for task_data in tasks_data:
            assigned_to_users = task_data.pop("assigned_to", [])
            task = Task.objects.create(
                project=project,
                assigned_by=assigned_by_user,
                **task_data,
            )
            if assigned_to_users:
                task.assigned_to.set(assigned_to_users)

        return project



#project image serializer
class ProjectImageSerializer(serializers.ModelSerializer):  
    class Meta:
        model = ProjectImages
        fields = ['id', 'project', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class ProjectFileSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = ProjectFile
        fields = ['id', 'project', 'project_name', 'file', 'uploaded_at']

        
class ProjectReadSerializer(serializers.ModelSerializer):
    members = ProjectMembersReadSerializer(source="projectmembers_set", many=True, read_only=True)
    tasks = TaskReadSerializer(source="task_set", many=True, read_only=True)
    project_images = ProjectImageSerializer(source="images", many=True, read_only=True)
    ptoject_files = ProjectFileSerializer(source="files", many=True, read_only=True)
    time_spent = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    assigned_by = serializers.SerializerMethodField()
    assigned_by_pic = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "project_logo",
            "project_name",
            "client",
            "created_at",
            'assigned_by',
            'assigned_by_pic',
            "start_date",
            "end_date",
            "priority",
            "project_value",
            "total_working_hours",
            "time_spent",
            "completed_tasks_count",
            "extra_time",
            "description",
            "status",
            "reason_for_rejection",
            "attachment",
            "members",
            "tasks",
            "project_images",
            "ptoject_files",
        ]


    def get_assigned_by(self, obj):
        return obj.assigned_by.first_name + " " + obj.assigned_by.last_name if obj.assigned_by else None   
    
    def get_assigned_by_pic(self, obj):
        if obj.assigned_by and hasattr(obj.assigned_by, 'employee_profile'):
            profile = obj.assigned_by.employee_profile
            if profile and profile.profile_pic:
                return profile.profile_pic.url
        return None
     
    def get_time_spent(self, obj):
        """
        Calculates the total time spent on this project
        based on all related tasks' updated_at fields.
        """
        from datetime import timedelta
        from django.utils import timezone

        now = timezone.now()
        total_time = timedelta()

        # Loop through all related tasks
        for task in obj.task_set.all():
            if task.updated_at:
                # Calculate time spent since last update or creation
                diff = now - task.updated_at
                total_time += diff

        # Combine project total working hours if available
        total_seconds = total_time.total_seconds()
        hours = round(total_seconds / 3600, 2)
        return f"{hours} hours"

    def get_completed_tasks_count(self, obj):
        """
        Counts how many tasks are completed for this project.
        """
        return obj.task_set.filter(status__iexact="completed").count()    


# leave list serializer 
class LeaveSerializerview(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    approved_by = serializers.StringRelatedField()

    class Meta:
        model = Leave
        fields = '__all__'

# Employee Daily Attendance Details Serializer
class EmployeeDailyAttendanceDetailsSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    session_duration_hours = serializers.SerializerMethodField()
    is_active_session = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'department', 'designation',
            'date', 'in_time', 'out_time', 'attendance_type', 'location', 
            'qr_scan', 'status', 'punch_in', 'session_duration_hours', 
            'is_active_session', 'created_at', 'updated_at'
        ]
    
    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_department(self, obj):
        return obj.employee.department
    
    def get_designation(self, obj):
        return obj.employee.designation
    
    def get_session_duration_hours(self, obj):
        if obj.out_time and obj.in_time:
            duration = obj.out_time - obj.in_time
            return round(duration.total_seconds() / 3600, 2)
        return None
    
    def get_is_active_session(self, obj):
        return obj.out_time is None and obj.punch_in
    

# employee notification serializer 
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "user",
            "title",    
            "action",
            "timestamp",
        ]    


class EmployeeGoogleFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeGoogleFormResponse
        fields = '__all__'