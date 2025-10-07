from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from . models import *


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
            "id", "accountNumber", "ifscCode", "branchName",
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

    class Meta:
        model = EmployeeDetail
        fields = [
            "id", "firstName", "lastName", "employeeId",
            "department", "designation", "repMgrTl", "is_team_lead",
            "salary", "email", "password", "confirmPassword",
            "profile_pic", "phone", "address", "dob","user_type","job_type",
            "gender", "nationality", "blood_group", "emergency_contact",
            # Bank fields
            "accountNumber", "confirmAccountNumber", "ifscCode",
            "branchName", "accountHolderName", "documents",
        ]

    def validate(self, data):
        if data["password"] != data["confirmPassword"]:
            raise serializers.ValidationError("Passwords do not match")
        if data.get("accountNumber") and data.get("accountNumber") != data.get("confirmAccountNumber"):
            raise serializers.ValidationError("Account numbers do not match")
        validate_email(data["email"])
        return data

    def create(self, validated_data):
        # Pull out non-model fields
        validated_data.pop("confirmPassword", None)
        raw_password = validated_data.pop("password")
        email = validated_data.pop("email")

        account_number = validated_data.pop("accountNumber", None)
        validated_data.pop("confirmAccountNumber", None)
        ifsc_code = validated_data.pop("ifscCode", None)
        branch_name = validated_data.pop("branchName", None)
        account_holder = validated_data.pop("accountHolderName", None)
        documents_files = validated_data.pop("documents", [])
        profile_pic_file = validated_data.pop("profile_pic", None)

        if profile_pic_file:
            validated_data["profile_pic"] = profile_pic_file

        # Create User
        user = User.objects.create(
            email=email,
            role="employee",
            password=make_password(raw_password),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),   
        )

        # Create EmployeeDetail
        employee = EmployeeDetail.objects.create(user=user, **validated_data)

        # Create BankDetail if provided
        if account_number:
            bank_detail = BankDetail.objects.create(
                employee=employee,
                account_number=account_number,
                ifsc_code=ifsc_code,
                branch_name=branch_name,
                account_holder=account_holder,
            )
            # Save uploaded documents
            for doc in documents_files:
                bank_detail.documents.save(doc.name, doc, save=True)

        return employee




class EmployeeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
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
            "latitude",       # ✅ instead of location
            "longitude", 
            "qr_scan",
            "selfie",
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
    class Meta:
        model = Leave
        fields = [
            "id",
            "user",
            "employee",
            "leave_type",
            "start_date",
            "end_date",
            "status",
            "approved_by",
            "attachments",
            "reason",
        ]

# project , task , members  serializer

class TaskSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = Task
        fields = ["id","title", "due_date","description", "assigned_by", "assigned_to", "status"]


class TaskReadSerializer(serializers.ModelSerializer):
    assigned_by_id = serializers.IntegerField(source="assigned_by.id", read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    assigned_to_id = serializers.IntegerField(source="assigned_to.id", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

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
            "due_date",
            "updated_at",
        ]

    def get_assigned_by_name(self, obj):
        return obj.assigned_by.email if obj.assigned_by else None

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.email if obj.assigned_to else None


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
    class Meta:
        model = ProjectMembers
        fields = ["id", "team_leader", "project_manager", "tags"]

class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMembersSerializer(write_only=True, many=True)  # expects list of dicts
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
        members_data = validated_data.pop("members")
        tasks_data = validated_data.pop("tasks")

        # Create Project
        project = Project.objects.create(**validated_data)

        # Create multiple ProjectMembers
        for member in members_data:
            ProjectMembers.objects.create(project=project, **member)

        # Create multiple Tasks
        request = self.context.get("request")
        assigned_by_user = getattr(request, "user", None) if request else None
        for task_data in tasks_data:
            Task.objects.create(
                project=project,
                assigned_by=assigned_by_user,
                **task_data,
            )

        return project


class ProjectReadSerializer(serializers.ModelSerializer):
    members = ProjectMembersReadSerializer(source="projectmembers_set", many=True, read_only=True)
    tasks = TaskReadSerializer(source="task_set", many=True, read_only=True)

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
            "status",
            "reason_for_rejection",
            "attachment",
            "members",
            "tasks",
        ]

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