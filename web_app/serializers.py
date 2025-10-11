from rest_framework import serializers
from core_app.models import *
from django.db.models import Min, Max,OuterRef,Subquery
import pytz
from datetime import date, timedelta 



# admin profile serializer
class AdminProfileSerializerView(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = '__all__'


class FilterNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = ['user_id','first_name', 'last_name', 'designation', 'email','phone','address','gender']
        
        
        
class ProjectManagerNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = ['user_id', 'first_name', 'last_name', 'designation', 'email', 'phone', 'address', 'gender']     
        
        
        
class EmployeeNameSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployeeDetail
        fields = ['user_id', 'first_name', 'last_name', 'designation', 'email', 'phone', 'address', 'gender']        


class EmployeebirthdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = '__all__'


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

# tasks list serializer 
class ProjectMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembers
        fields = ["team_leader", "project_manager", "tags"]

class TaskWithMembersSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    project_members = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status",
            "assigned_by", "assigned_to", "created_at", "updated_at",
            "project_name", "project_members"
        ]

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
        read_only_fields = ['id', 'added_by','type']  # 'added_by' will be set in the view


# department serializer
class DepartmentSerializer(serializers.ModelSerializer):
    department_head = serializers.CharField(source='department_head.first_name', read_only=True)
    department_head_id = serializers.CharField(source='department_head.id', read_only=True)
    class Meta:
        model = Department
        fields = ['id', 'name', 'description','department_head','department_head_id']        


# designation serializer
class DesignationSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.CharField(source='department.id', read_only=True)
    class Meta:
        model = Designation
        fields = ['id', 'title', 'department','description','department_id']        


class NotificationLogSerializer(serializers.ModelSerializer):
    # Include user ID and username in the serialized output
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    # Convert timestamp to Indian time
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = ['id', 'user_id', 'user_name', 'action', 'title', 'timestamp']

    def get_timestamp(self, obj):
        # Convert UTC timestamp to IST
        ist = pytz.timezone('Asia/Kolkata')
        return obj.timestamp.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
    

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
    leave_count = serializers.IntegerField()
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
