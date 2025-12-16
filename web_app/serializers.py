from rest_framework import serializers
from core_app.models import *
from django.db.models import Min, Max,OuterRef,Subquery
import pytz
from datetime import date, timedelta ,datetime , time
from core_app.serializers import *
from django.utils.timezone import is_aware, make_naive, now



# admin profile serializer
class AdminProfileSerializerView(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = '__all__'


class FilterNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = ['user_id','first_name', 'last_name', 'designation', 'user_type','email','phone','address','gender']
        
        
        
class ProjectManagerNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = ['user_id', 'first_name', 'last_name', 'designation', 'user_type','email', 'phone', 'address', 'gender']     
        
        
        
class EmployeeNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    id = serializers.CharField(source='user.id', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)


    class Meta:
        model = EmployeeDetail
        fields = ['id', 'user_role','first_name', 'last_name', 'designation', 'email', 'phone', 'address', 'gender']        


class EmployeebirthdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = ['id', 'first_name', 'last_name','dob', 'user_type','designation','department','phone','profile_pic']


class AttendanceSummarySerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()


class EmployeeListSerializerAdminView(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    attendance_status = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    joiningYear = serializers.SerializerMethodField()
   
    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "user_id",
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "designation",
            "department",
            "attendance_status",
            "profile_pic",
            "joiningYear",
           
        ]

    def get_attendance_status(self, obj):
        today = self.context.get("today")
        attendance = Attendance.objects.filter(employee=obj, date=today).first()
        if attendance and attendance.status == "Present":
            return "Active"
        return "Inactive"

    def get_status(self, obj):
        return True

    def get_message(self, obj):
        return "Data fetched successfully"   
    def get_joiningYear(self, obj):
        """Return the joining year as an integer (e.g. 2023) or None if unavailable."""
        created = getattr(obj, "created_at", None)
        if created:
            try:
                return created.year
            except Exception:
                return None
        return None


# employee active inactive employees list serializer
class EmployeeActiveInactiveListSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)


    class Meta:
        model = EmployeeDetail  
        fields = ['employee_id','first_name','last_name','designation','department','profile_pic','user_type','emp_exit_date','emp_status','is_active']

# tasks list serializer 
class ProjectMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembers
        fields = ["team_leader", "project_manager", "tags"]

class TaskWithMembersSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    project_members = serializers.SerializerMethodField()
    coordinator = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    assigned_by_name = serializers.CharField(source='assigned_by.first_name', read_only=True)
    assignee_name = serializers.CharField(source='assigned_to.first_name', read_only=True)
    assigned_by_pic = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    start_date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M:%S', read_only=True)
    end_date = serializers.DateField(source='due_date', format='%Y-%m-%d', read_only=True)

    hours_worked = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "end_date","status","coordinator",
            "assigned_by", "assigned_to", "start_date", "updated_at",
            "project_name", "project_members","assigned_by_name","assignee_name","assigned_by_pic","assignee","hours_worked"
        ]

    def get_coordinator(self, obj):
    
      project_member = ProjectMembers.objects.filter(project=obj.project).first()
      if project_member:
        return NewProjectMembersReadSerializer(
            project_member, context=self.context
        ).data.get("project_manager_details")
      return None    

    def get_project_members(self, obj):
        if obj.project:
            members = ProjectMembers.objects.filter(project=obj.project).first()
            if members:
                return ProjectMembersSerializer(members).data
        return None

    def get_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None

    def get_updated_at(self, obj):
        if obj.updated_at:
            return obj.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None
    

    def get_hours_worked(self, obj):
        """Calculate hours between created_at (aware datetime) and due_date (date)."""
        if obj.created_at and obj.due_date:
            # Convert due_date to datetime at end of day
            due_datetime = datetime.combine(obj.due_date, time.max)

            # Make due_datetime timezone-aware like created_at
            if obj.created_at.tzinfo:
                due_datetime = due_datetime.replace(tzinfo=obj.created_at.tzinfo)

            delta = due_datetime - obj.created_at
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    # ✅ New methods for profile pics
    def get_assigned_by_pic(self, obj):
        if obj.assigned_by and hasattr(obj.assigned_by, "employee_profile"):
            profile = obj.assigned_by.employee_profile
            if profile.profile_pic:
                request = self.context.get("request")
                url = profile.profile_pic.url
                return request.build_absolute_uri(url) if request else url
        return None

    # def get_assignee(self, obj):
    #     if obj.assigned_to and hasattr(obj.assigned_to, "employee_profile"):
    #         profile = obj.assigned_to.employee_profile
    #         if profile.profile_pic:
    #             request = self.context.get("request")
    #             url = profile.profile_pic.url
    #             return request.build_absolute_uri(url) if request else url
    #     return None
    def get_assignee(self, obj):
        assignee_list = []
        request = self.context.get("request")

        for user in obj.assigned_to.all():
            profile_pic_url = None
            if hasattr(user, "employee_profile") and user.employee_profile.profile_pic:
                url = user.employee_profile.profile_pic.url
                profile_pic_url = request.build_absolute_uri(url) if request else url

            assignee_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "profile_pic": profile_pic_url,
            })

        return assignee_list
    
    # serializer for listing all tasks 
class ListTaskWithMembersSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    # project_members = serializers.SerializerMethodField()
    coordinator = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    assigned_by_name = serializers.CharField(source='assigned_by.first_name', read_only=True)
    assignee_name = serializers.CharField(source='assigned_to.first_name', read_only=True)
    assigned_by_pic = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    start_date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M:%S', read_only=True)
    end_date = serializers.DateField(source='due_date', format='%Y-%m-%d', read_only=True)

    hours_worked = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "end_date","status","coordinator",
            "assigned_by", "assigned_to", "start_date", "updated_at",
            "project_name","assigned_by_name","assignee_name","assigned_by_pic","assignee","hours_worked","priority"
        ]

    def get_coordinator(self, obj):
    
      project_member = ProjectMembers.objects.filter(project=obj.project).first()
      if project_member:
        return NewProjectMembersReadSerializer(
            project_member, context=self.context
        ).data.get("project_manager_details")
      return None    

    def get_project_members(self, obj):
        if obj.project:
            members = ProjectMembers.objects.filter(project=obj.project).first()
            if members:
                return ProjectMembersSerializer(members).data
        return None

    def get_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None

    def get_updated_at(self, obj):
        if obj.updated_at:
            return obj.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        return None
    

    def get_hours_worked(self, obj):
        """Calculate hours between created_at (aware datetime) and due_date (date)."""
        if obj.created_at and obj.due_date:
            # Convert due_date to datetime at end of day
            due_datetime = datetime.combine(obj.due_date, time.max)

            # Make due_datetime timezone-aware like created_at
            if obj.created_at.tzinfo:
                due_datetime = due_datetime.replace(tzinfo=obj.created_at.tzinfo)

            delta = due_datetime - obj.created_at
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    # ✅ New methods for profile pics
    def get_assigned_by_pic(self, obj):
        if obj.assigned_by and hasattr(obj.assigned_by, "employee_profile"):
            profile = obj.assigned_by.employee_profile
            if profile.profile_pic:
                request = self.context.get("request")
                url = profile.profile_pic.url
                return request.build_absolute_uri(url) if request else url
        return None

    def get_assignee(self, obj):
        assignee_list = []
        request = self.context.get("request")

        for user in obj.assigned_to.all():
            profile_pic_url = None
            if hasattr(user, "employee_profile") and user.employee_profile.profile_pic:
                url = user.employee_profile.profile_pic.url
                profile_pic_url = request.build_absolute_uri(url) if request else url

            assignee_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "profile_pic": profile_pic_url,
            })

        return assignee_list
    


class ProjectMemberslistSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = ProjectMembers
        fields = ['id', 'project_name', 'team_leader', 'project_manager', 'tags']

class EmployeeDetaileditSerializer(serializers.ModelSerializer):
    taken = serializers.SerializerMethodField()
    total_leaves = serializers.SerializerMethodField()
    absent = serializers.SerializerMethodField()
    request = serializers.SerializerMethodField()
    lossofpay = serializers.SerializerMethodField()
    workeddays = serializers.SerializerMethodField()
    bank_details = BankDetailSerializer(many=True, required=False)

    class Meta:
        model = EmployeeDetail
        fields = "__all__"
        extra_fields = [
            "leaves", "taken", "total_leaves", "absent",
            "request", "lossofpay", "workeddays", "bank_details"
        ]

    # --- Custom Fields ---
    def get_taken(self, obj):
        approved_count = Leave.objects.filter(employee=obj, status="Approved").count()
        return approved_count if approved_count > 0 else "No leave taken"

    def get_request(self, obj):
        pending_count = Leave.objects.filter(employee=obj, status="Pending").count()
        return pending_count if pending_count > 0 else "No leave in request"

    def get_total_leaves(self, obj):
        return 16  # static

    def get_absent(self, obj):
        return 2  # static

    def get_workeddays(self, obj):
        return 240  # static

    def get_lossofpay(self, obj):
        return 2  # static

    # --- Custom Update for nested Bank Details ---
    def update(self, instance, validated_data):
        bank_data_list = validated_data.pop("bank_details", None)

        # Update Employee basic details
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Bank Details if provided
        if bank_data_list is not None:
            # Clear old bank details and re-add
            BankDetail.objects.filter(employee=instance).delete()
            for bank_data in bank_data_list:
                BankDetail.objects.create(employee=instance, **bank_data)

        return instance



# employee attendance details by id
class DailyAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    in_time = serializers.DateTimeField()
    out_time = serializers.DateTimeField()
    status = serializers.CharField()
    total_time = serializers.SerializerMethodField()
    overtime = serializers.SerializerMethodField()

    def get_total_time(self, instance):
        in_time = instance.get("in_time")
        out_time = instance.get("out_time")

        if in_time and out_time:
            total_time = out_time - in_time
            hours, remainder = divmod(total_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"

    def get_overtime(self, instance):
        out_time = instance.get("out_time")
        if out_time:
            cutoff = out_time.replace(hour=18, minute=0, second=0, microsecond=0)
            if out_time > cutoff:
                overtime = out_time - cutoff
                hours, remainder = divmod(overtime.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                return f"{hours}h {minutes}m"
        return "0h 0m"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        ist = pytz.timezone("Asia/Kolkata")

        in_time = instance.get("in_time")
        out_time = instance.get("out_time")

        # Convert datetime to IST string format
        if in_time:
            in_time = timezone.localtime(in_time, ist)
            data["in_time"] = in_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data["in_time"] = None

        if out_time:
            out_time = timezone.localtime(out_time, ist)
            data["out_time"] = out_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data["out_time"] = None

        return data
class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    attendances = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDetail
        fields = ["id", "first_name", "last_name", "profile_pic", "employee_id", "attendances"]

    def get_attendances(self, obj):
        latest_status = (
            Attendance.objects.filter(employee=obj, date=OuterRef("date"))
            .order_by("-out_time")
            .values("status")[:1]
        )

        qs = (
            Attendance.objects.filter(employee=obj)
            .values("date")
            .annotate(
                in_time=Min("in_time"),
                out_time=Max("out_time"),
                status=Subquery(latest_status),
            )
            .order_by("-date")
        )

        return DailyAttendanceSerializer(qs, many=True).data        
    
# holiday serializer
class HolidaySerializer1(serializers.ModelSerializer):
    # Show added_by user email (or full name if you want)
    added_by = serializers.CharField(source='added_by.first_name', read_only=True)

    class Meta:
        model = Holiday
        fields = ['id', 'description', 'date', 'type','added_by'] 
        read_only_fields = ['id', 'added_by','type']  


# department serializer
class DepartmentSerializer(serializers.ModelSerializer):
    department_head = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    # These are read-only extras for displaying name and id in responses
    department_head_name = serializers.CharField(source='department_head.first_name', read_only=True)
    department_head_id = serializers.CharField(source='department_head.id', read_only=True)
    class Meta:
        model = Department
        fields = ['id', 'name', 'description','department_head','department_head_name','department_head_id']    
            


# designation serializer
class DesignationSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True
    )
    class Meta:
        model = Designation
        fields = ['id', 'title', 'department','description','department_id']        


class NotificationLogSerializer(serializers.ModelSerializer):
    # Include user ID and username in the serialized output
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()



    # Convert timestamp to Indian time
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = ['id','user_id','employee_id','user_name','action', 'title', 'timestamp']

    def get_timestamp(self, obj):
        # Convert UTC timestamp to IST
        ist = pytz.timezone('Asia/Kolkata')
        return obj.timestamp.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
    
    def get_user_name(self, obj):

        return f"{obj.user.first_name} {obj.user.last_name}".strip()   
    
    def get_employee_id(self, obj):
      
        try:
            emp = EmployeeDetail.objects.get(user=obj.user)
            return emp.id
        except EmployeeDetail.DoesNotExist:
            return None
    

class AttendanceEditSerializer(serializers.ModelSerializer):
    total_time = serializers.SerializerMethodField()
    overtime = serializers.SerializerMethodField()
    break_time = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ["id", "employee", "date", "in_time", "out_time", "status", "total_time", "overtime", "break_time"]

    def validate(self, data):
        in_time = data.get("in_time")
        out_time = data.get("out_time")

        if in_time and out_time and out_time < in_time:
            raise serializers.ValidationError("Out time cannot be earlier than In time.")
        return data

    # ✅ Compute total working time
    def get_total_time(self, obj):
        in_time = obj.in_time
        out_time = obj.out_time
        if in_time and out_time:
            total_time = out_time - in_time
            hours, remainder = divmod(total_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"

    # ✅ Compute overtime (after 6:00 PM)
    def get_overtime(self, obj):
        out_time = obj.out_time
        if out_time:
            cutoff = out_time.replace(hour=18, minute=0, second=0, microsecond=0)
            if out_time > cutoff:
                overtime = out_time - cutoff
                hours, remainder = divmod(overtime.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                return f"{hours}h {minutes}m"
        return "0h 0m"

    # ✅ Static break time (1 hour 5 minutes)
    def get_break_time(self, obj):
        return "1h 5m"

    # ✅ Format in_time and out_time in IST
    def to_representation(self, instance):
        data = super().to_representation(instance)
        ist = pytz.timezone("Asia/Kolkata")

        in_time = instance.in_time
        out_time = instance.out_time

        if in_time:
            in_time = timezone.localtime(in_time, ist)
            data["in_time"] = in_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data["in_time"] = None

        if out_time:
            out_time = timezone.localtime(out_time, ist)
            data["out_time"] = out_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data["out_time"] = None

        return data    

class EmployeeDetailWithLeaveSerializer(serializers.ModelSerializer):
    taken = serializers.SerializerMethodField()
    total_leaves = serializers.SerializerMethodField()
    absent = serializers.SerializerMethodField()
    request = serializers.SerializerMethodField()
    lossofpay = serializers.SerializerMethodField()
    workeddays = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDetail
        fields = "__all__"
        extra_fields = [
            "leaves", "taken", "total_leaves", "absent",
            "request", "lossofpay", "workeddays", "bank_details"
        ]

    def get_taken(self, obj):
        approved_count = Leave.objects.filter(employee=obj, status="Approved").count()
        return approved_count if approved_count > 0 else "No leave taken"

    def get_request(self, obj):
        pending_count = Leave.objects.filter(employee=obj, status="Pending").count()
        return pending_count if pending_count > 0 else "No leave in request"

    def get_total_leaves(self, obj):
        return 16   # static for now

    def get_absent(self, obj):
        return 2    # static for now

    def get_workeddays(self, obj):
        return 240  # static for now

    def get_lossofpay(self, obj):
        return 2    # static for now

    def get_bank_details(self, obj):
        bank_details = BankDetail.objects.filter(employee=obj)
        if bank_details.exists():
            return BankDetailSerializer(bank_details, many=True).data
        return "No bank details found"

      
class EmployeeAttendanceSerializerpast7days(serializers.ModelSerializer):
    attendances = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDetail
        fields = ["id", "first_name", "last_name", "profile_pic", "employee_id", "attendances"]

    def get_attendances(self, obj):
        today = date.today()
        last_7_days = today - timedelta(days=7)

        # Filter attendance only for the past 7 days (including today)
        attendance_qs = Attendance.objects.filter(
            employee=obj,
            date__range=[last_7_days, today]
        )

        # Subqueries for latest status and ID of the day's last record
        latest_status = (
            Attendance.objects.filter(employee=obj, date=OuterRef("date"))
            .order_by("-out_time")
            .values("status")[:1]
        )
        latest_attendance_id = (
            Attendance.objects.filter(employee=obj, date=OuterRef("date"))
            .order_by("-out_time")
            .values("id")[:1]
        )

        # Annotate daily summary
        qs = (
            attendance_qs
            .values("date")
            .annotate(
                id=Subquery(latest_attendance_id),
                in_time=Min("in_time"),
                out_time=Max("out_time"),
                status=Subquery(latest_status),
            )
            .order_by("-date")
        )

        return DailyAttendanceSerializer(qs, many=True).data

# branch serializer
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        # fields = ['id', 'name', 'location', 'description']    


class AttendanceLeaveSummarydiagramSerializer(serializers.Serializer):
    absent_count = serializers.IntegerField()
   # leave_count = serializers.IntegerField()
    sick_leave_count = serializers.IntegerField()
    wfh_count = serializers.IntegerField()
    on_time_count = serializers.IntegerField()
    late_count = serializers.IntegerField() 



class WorkinghoursfractionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    today_total_hours = serializers.SerializerMethodField()  # new field

    class Meta:
        model = Attendance
        fields = [
            'id',
            'employee_name',
            'in_time',
            'out_time',
            'today_total_hours',  # include total hours in response
        ]

    def get_today_total_hours(self, obj):
        if obj.in_time and obj.out_time:
            delta = obj.out_time - obj.in_time
            worked_hours = delta.total_seconds() / 3600  # convert seconds to hours
            worked_hours_rounded = round(worked_hours, 2)
            # return as fraction of 9-hour day (adjust as needed)
            return f"{worked_hours_rounded} / 9 hrs"
        return "0.0 / 9 hrs"
    
    
    
class WeeklyWorkinghoursSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    weekly_total_hours = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'employee_name',
            'weekly_total_hours',
        ]

    def get_weekly_total_hours(self, obj):
        # 'obj' will be Attendance instance but we'll use context to pass total
        total_seconds = getattr(obj, 'weekly_seconds', 0)
        worked_hours = total_seconds / 3600
        worked_hours_rounded = round(worked_hours, 2)
        return f"{worked_hours_rounded} / 45 hrs"  # Assuming 9hrs/day * 5days


# privacy policy serializers
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = '__all__'


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditions
        fields = '__all__'        

class AboutsessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = '__all__'        

#  leave diagram serializer
class LeavediagramSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(source='employee.first_name', read_only=True)
    employee_last_name = serializers.CharField(source='employee.last_name', read_only=True)

    is_team_lead_status = serializers.SerializerMethodField()
    is_project_leader_status = serializers.SerializerMethodField()
    is_hr_status = serializers.SerializerMethodField()
    is_ceo_status = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = [
            'id',
            'employee_first_name',
            'employee_last_name',
            'leave_type',
            'start_date',
            'end_date',
            'status',
            'is_team_lead_status',
            'is_project_leader_status',
            'is_hr_status',
            'is_ceo_status',
        ]

    # ✅ Status helpers (Approved / Rejected / Pending)
    def get_is_team_lead_status(self, obj):
        if obj.is_team_lead_rejected:
            return "Rejected"
        elif obj.is_team_lead_approved:
            return "Approved"
        return "Pending"

    def get_is_project_leader_status(self, obj):
        if obj.is_project_leader_rejected:
            return "Rejected"
        elif obj.is_project_leader_approved:
            return "Approved"
        return "Pending"

    def get_is_hr_status(self, obj):
        if obj.is_hr_rejected:
            return "Rejected"
        elif obj.is_hr_approved:
            return "Approved"
        return "Pending"

    def get_is_ceo_status(self, obj):
        if obj.is_ceo_rejected:
            return "Rejected"
        elif obj.is_ceo_approved:
            return "Approved"
        return "Pending"        
    
# serializers.py
class ProjectManagerSearchListSerializer(serializers.ModelSerializer):
    id =  serializers.CharField(source='user.id', read_only=True)
    
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "full_name",
            "designation",
            "department",
            "profile_pic",
            "user_type",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()    
    
class TeamLeaderSearchSerializer(serializers.ModelSerializer):
    id =  serializers.CharField(source='user.id', read_only=True)
    full_name = serializers.SerializerMethodField()
    company_branch_name = serializers.CharField(source="company_branch.branch_name", read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "full_name",
            "user_type",
            "company_branch_name",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()    
    
class EmployeeSearchSerializer(serializers.ModelSerializer):
    id =  serializers.CharField(source='user.id', read_only=True)
    full_name = serializers.SerializerMethodField()
    company_branch_name = serializers.CharField(source="company_branch.branch_name", read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "full_name",
            "user_type",
            "company_branch_name",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class CeoctoSearchSerializer(serializers.ModelSerializer):
    id =  serializers.CharField(source='user.id', read_only=True)
    full_name = serializers.SerializerMethodField()
    company_branch_name = serializers.CharField(source="company_branch.branch_name", read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "full_name",
            "user_type",
            "company_branch_name",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
# ---------------------------
# Task Serializer (limited)
# ---------------------------
class LimitedTaskSerializer(serializers.ModelSerializer):
    task_hours = serializers.SerializerMethodField()
    current_progress = serializers.SerializerMethodField()
    assigned_employee = serializers.SerializerMethodField()  

    class Meta:
        model = Task
        fields = ["task_hours", "current_progress", "assigned_employee"]

    def _to_datetime(self, dt):
        """Convert date to datetime and make timezone naive if needed."""
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time.min)  # convert date → datetime
        if is_aware(dt):
            dt = make_naive(dt)  # only convert aware → naive
        return dt

    def get_task_hours(self, obj):
        """Total available hours between created_at and due_date."""
        if obj.created_at and obj.due_date:
            start = self._to_datetime(obj.created_at)
            end = self._to_datetime(obj.due_date)
            delta = end - start
            return round(delta.total_seconds() / 3600, 2)
        return None

    def get_current_progress(self, obj):
        """Shows how much time has passed (in hours and percentage)."""
        if obj.created_at and obj.due_date:
            start = self._to_datetime(obj.created_at)
            end = self._to_datetime(obj.due_date)

            total_seconds = (end - start).total_seconds()
            elapsed_seconds = (self._to_datetime(now()) - start).total_seconds()

            if total_seconds <= 0:
                return "0 / 0 hours (0%)"

            progress_fraction = elapsed_seconds / total_seconds
            progress_fraction = max(0.0, min(progress_fraction, 1.0))  # clamp 0–1

            total_hours = round(total_seconds / 3600, 2)
            current_hours = round(elapsed_seconds / 3600, 2)
            return f"{current_hours} / {total_hours} hours ({round(progress_fraction * 100, 1)}%)"
        return None

    def get_assigned_employee(self, obj):
        """Return list of assigned employees (since assigned_to is ManyToMany)."""
        employees = []
        request = self.context.get("request")

        for user in obj.assigned_to.all():  # ✅ iterate through all assigned users
            emp = EmployeeDetail.objects.filter(user=user).first()
            if emp:
                employees.append({
                    "id": emp.id,
                    "user_id": emp.user.id,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "designation": emp.designation,
                    "profile_pic": (
                        request.build_absolute_uri(emp.profile_pic.url)
                        if request and emp.profile_pic else None
                    ),
                })
        return employees


# ---------------------------
# Project Members Read Serializer
# ---------------------------
class NewProjectMembersReadSerializer(serializers.ModelSerializer):
    # team_members = serializers.SerializerMethodField()
    project_manager_details = serializers.SerializerMethodField()
    team_leader_details = serializers.SerializerMethodField()
    tags_details = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembers
        fields = [
            "team_leader_details",
            "project_manager_details",
            "tags_details",
            # "team_members"
        ]

    # -------------------------------
    # Helper to get full employee info
    # -------------------------------
    def get_employee_info(self, emp_id):
    # """Return basic employee info (id, name, designation, profile_pic)."""
      try:
          emp = EmployeeDetail.objects.get(user=emp_id)
          request = self.context.get("request")  # safer
          return {
              "id": emp.id,
              "user_id": emp.user.id,
              "name": f"{emp.first_name} {emp.last_name}",
              "designation": emp.designation,
              "profile_pic": request.build_absolute_uri(emp.profile_pic.url) if request and emp.profile_pic else None,
          }
      except EmployeeDetail.DoesNotExist:
          return None


    # --------------------------------
    # Project Manager (Coordinator)
    # --------------------------------
    def get_project_manager_details(self, obj):
        data = obj.project_manager
        if not data:
            return None

        if isinstance(data, dict):
            emp_id = data.get("id")
        elif isinstance(data, int):
            emp_id = data
        else:
            emp_id = None

        return self.get_employee_info(emp_id)

    # --------------------------------
    # Team Leader
    # --------------------------------
    def get_team_leader_details(self, obj):
        data = obj.team_leader
        if not data:
            return None

        if isinstance(data, dict):
            emp_id = data.get("id")
        elif isinstance(data, int):
            emp_id = data
        else:
            emp_id = None

        return self.get_employee_info(emp_id)
    
    def get_tags_details(self , obj):
        data = obj.tags
        if not data:
            return None
        if isinstance(data, dict):
            emp_id = data.get("id")
        elif isinstance(data, int):
            emp_id = data
        else:
            emp_id = None
        return self.get_employee_info(emp_id)    


    # --------------------------------
    # Team Members with assigned tasks
    # --------------------------------
    # def get_team_members(self, obj):
    #     project = obj.project
    #     members_list = []

    #     # Collect IDs from tags (which store team members)
    #     tag_data = obj.tags or []
    #     if not isinstance(tag_data, list):
    #         return []

    #     for member in tag_data:
    #         if isinstance(member, dict):
    #             emp_id = member.get("id")
    #         elif isinstance(member, int):
    #             emp_id = member
    #         else:
    #             emp_id = None

    #         emp_info = self.get_employee_info(emp_id)
    #         if emp_info:
    #             # Find tasks assigned to this employee’s user
    #             tasks = Task.objects.filter(
    #                 project=project,
    #                 assigned_to=emp_info["user"]
    #             ).values("title", "status")

    #             emp_info["assigned_tasks"] = list(tasks)
    #             members_list.append(emp_info)

    #     return members_list


# ---------------------------
# Project Serializer (limited)
# ---------------------------
class NewProjectReadSerializer(serializers.ModelSerializer):
    members = NewProjectMembersReadSerializer(source="projectmembers_set", many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    coordinator = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "project_name",
            "start_date",
            "end_date",
            "status",
            "coordinator",  
            "members",    
            "tasks",
        ]

    def get_coordinator(self, obj):
        """Fetch project manager from ProjectMembers JSON by ID."""
        project_member = ProjectMembers.objects.filter(project=obj).first()
        if project_member:
            return NewProjectMembersReadSerializer(
                project_member, context=self.context
            ).data.get("project_manager_details")
        return None

    def get_tasks(self, obj):
        tasks = obj.task_set.all().order_by("-id")
        return LimitedTaskSerializer(tasks, many=True).data


# shifts serializer  
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTable
        fields = '__all__'
        read_only_fields = ['id']


class WorksheetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = Worksheet
        fields = [
            "id",
            "title",
            "file",
            "file_url",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
            "file_size"
        ]
        read_only_fields = ["uploaded_by", "uploaded_at", "file_size"]

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None    
    
    
    
class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = [
            "id",
            "title",
            "department",
            "description",
            "is_pinned",
            "date",
            "created_by",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["id","is_pinned", "created_by", "created_at", "updated_at"]        


class TrainingVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingVideo
        fields = "__all__"
        read_only_fields = ["id", "views", "uploaded_at", "updated_at"]        


class ShiftviewSerializer(serializers.ModelSerializer):
    punch_in = serializers.SerializerMethodField()
    punch_out = serializers.SerializerMethodField()
    break_start = serializers.SerializerMethodField()
    break_end = serializers.SerializerMethodField()
    lunch_start = serializers.SerializerMethodField()
    lunch_end = serializers.SerializerMethodField()

    class Meta:
        model = ShiftTable
        fields = [
            "id",
            "shifts_name",

            "punch_in",
            "punch_out",

            "break_start",
            "break_end",

            "lunch_start",
            "lunch_end",

            "created_at",
            "updated_at",
        ]

    # ----- COMMON FORMATTER -----
    def format_time(self, time_obj):
        if not time_obj:
            return None
        return time_obj.strftime("%I:%M %p")   

    # ----- MAIN SHIFT TIMES -----
    def get_punch_in(self, obj):
        return self.format_time(obj.start_time)

    def get_punch_out(self, obj):
        return self.format_time(obj.end_time)

    # ----- BREAK TIMES -----
    def get_break_start(self, obj):
        return self.format_time(obj.break_start)

    def get_break_end(self, obj):
        return self.format_time(obj.break_end)

    # ----- LUNCH TIMES -----
    def get_lunch_start(self, obj):
        return self.format_time(obj.lunch_start)

    def get_lunch_end(self, obj):
        return self.format_time(obj.lunch_end)
    


# FeedbackQuestionFormSerializer  serializer   
class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'order']
        read_only_fields = ['id']

class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'question_text',
            'question_type',
            'is_required',
            'order',
            'options'
        ]

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        question = Question.objects.create(**validated_data)

        for option in options_data:
            QuestionOption.objects.create(question=question, **option)

        return question


class FormSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Form
        fields = [
            'id',
            'title',
            'description',
            'is_active',
            'created_at',
            'questions'
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        form = Form.objects.create(**validated_data)

        for question_data in questions_data:
            QuestionSerializer().create({
                **question_data,
                "form": form
            })

        return form




class ShiftaddonSerializer(serializers.ModelSerializer):
    teams_name = serializers.CharField(source='team.name', read_only=True)
    class Meta:
        model = Shiftaddon
        fields = '__all__'
        read_only_fields = ['id' , 'teams_name']

