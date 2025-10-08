
from enum import auto
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


# Create your models here.


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, role="employee", password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # 👇 role always superadmin
        return self.create_user(
            email=email,
            role="superadmin",
            password=password,
            **extra_fields
        )
        

# ---------------------------
# User Model
# ---------------------------


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('superadmin', 'Superadmin'),
        ('admin', 'Admin (Team Lead)'),
        ('employee', 'Employee'),
    )

    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    first_name = models.CharField(max_length=100,null=True,blank=True)
    last_name = models.CharField(max_length=100,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Fix the reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',   # changed from default 'user_set'
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # changed from default 'user_set'
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"
    
    
# ---------------------------
# Employee Detail
# ---------------------------
class EmployeeDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    reporting_manager = models.CharField(max_length=100, blank=True, null=True)      
    is_team_lead = models.BooleanField(default=False)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    face_encoding = models.JSONField(blank=True, null=True)
    emp_status = models.CharField(max_length=100, blank=True, null=True)
    emp_exit_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

# ---------------------------
# OTP Verification (Email OTP)
# ---------------------------
class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=50, default="login")  # login / reset_password
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # ✅ new field
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.user.email} ({self.purpose})"

# ---------------------------
# Login History
# ---------------------------
class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_logs")
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Success")  # Success / Failed

    def __str__(self):
        return f"{self.user.email} - {self.status} ({self.login_time})"



# ---------------------------
# QR Session (QR codes generated by Admin)
# ---------------------------
class QR_Session(models.Model):
    code = models.CharField(max_length=255, default="DEFAULT_CODE")
    latitudes = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    


    

    def __str__(self):
        return f"QR {self.id} - {self.code}"
    # def save(self, *args, **kwargs):
    #     # Always reset expiry to 15 minutes from creation if not already set
    #     if not self.expires_at:
    #         self.expires_at = timezone.now() + timedelta(minutes=15)
    #     super().save(*args, **kwargs)

    # def is_expired(self):
    #     """Check if this QR is expired"""
    #     return timezone.now() > self.expires_at if self.expires_at else False   


# ---------------------------
# Attendance
# ---------------------------
class Attendance(models.Model):
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
    date = models.DateField()
    in_time = models.DateTimeField(blank=True, null=True)
    out_time = models.DateTimeField(blank=True, null=True)
    attendance_type = models.CharField(max_length=20)  # office / wfh
    location = models.CharField(max_length=255, blank=True, null=True)
    qr_scan = models.BooleanField(default=False)
    qrsession = models.ForeignKey("QR_Session", on_delete=models.SET_NULL, null=True, blank=True)  # ✅ fixed
    selfie = models.ImageField(upload_to="attendance_selfies/", blank=True, null=True)
    status = models.CharField(max_length=20)  # Present / Absent
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="verified_attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    punch_in = models.BooleanField(default=False)
    # half_time = models.CharField(null=True , blank=True)


    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.status})"

# ---------------------------
# Leave
# ---------------------------
class Leave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE,null=True,blank=True)
    requested_date = models.DateField(default=timezone.now)
    leave_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default="Pending")  # Pending / Approved / Rejected
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approved_leaves")
    attachments = models.FileField(upload_to="leave_attachments/", blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.status})"


# ---------------------------
# Holiday
# ---------------------------
class Holiday(models.Model):
    description = models.CharField(max_length=200)
    date = models.DateField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)  # Optional field

    def save(self, *args, **kwargs):
        # If type not set, default to Company Holiday
        if not self.type:
            self.type = 'Company Holiday' if self.added_by else 'Public Holiday'
        super().save(*args, **kwargs)


# Project 
class Project(models.Model):
    project_logo = models.FileField(upload_to="project_logo/")
    project_name = models.CharField(max_length=100)
    client = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    priority = models.CharField(100)
    project_value = models.CharField(100,null=True , blank =True)
    total_working_hours = models.CharField(max_length=50)
    extra_time = models.CharField(max_length=60,null=True , blank =True)
    description = models.TextField()
    attachment = models.FileField(upload_to="Project_attachment/")
    status = models.CharField(max_length = 100 , default='Pending')
    reason_for_rejection = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="projects_assigned")

    def __str__(self):
        return self.project_name


# project members
class ProjectMembers(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    team_leader = models.JSONField()
    project_manager = models.JSONField()
    tags = models.JSONField(null=True,blank=True)

    def __str__(self):
        return self.project.project_name


# ---------------------------
# Task
# ---------------------------
class Task(models.Model):
    project = models.ForeignKey(Project , on_delete=models.CASCADE,null=True , blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="tasks_assigned")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="tasks_received")
    status = models.CharField(max_length=50, default="Pending")  # Pending / In Progress / Completed
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

# ---------------------------
# NotificationLog
# ---------------------------
class NotificationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100,null=True,blank=True)
    action = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)  # Unread / Read
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email} at {self.timestamp}"

# ---------------------------
# BankDetail
# ---------------------------
class BankDetail(models.Model):
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=150)
    documents = models.FileField(upload_to="bank_docs/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# ---------------------------
# SalaryHistory
# ---------------------------
class SalaryHistory(models.Model):
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()


#---------------------------
# department

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True,blank=True)
    department_head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="headed_departments")

    def __str__(self):
        return self.name

#---------------------------    
# designation
class Designation(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="designations")
    description = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.title    
    

  # new branch table  
class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    google_map_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address = models.TextField(null=True,blank=True)
    status = models.CharField(max_length=20, default="Active")  # Active / Inactive
    starting_time = models.TimeField(null=True,blank=True)
    closing_time = models.TimeField(null=True,blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    company_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name  