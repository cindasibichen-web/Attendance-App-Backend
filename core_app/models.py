
from enum import auto
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from core_app.utils.encrypt_decrypt_data import *

# Create your models here.


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        """
        Override Django's default lookup so that authentication can match
        decrypted email values.
        """
        # Normalize user input email
        email = self.normalize_email(email)

        # Loop through all users and match by decrypted email
        for user in self.model.objects.all():
            decrypted = user.email  # If your EncryptedEmailField returns decrypted value on access
            if decrypted.lower() == email.lower():
                return user

        raise self.model.DoesNotExist(f"User with email {email} does not exist")
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

    email = EncryptedEmailField(unique=True, db_index=True)
    first_name = EncryptedCharField(max_length=600,null=True,blank=True)
    last_name = EncryptedCharField(max_length=600,null=True,blank=True)
    role = models.CharField(max_length=200, choices=ROLE_CHOICES, db_index=True)
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
    
# new branch table  
class Branch(models.Model):
    name = EncryptedCharField(max_length=600)
    location = EncryptedCharField(max_length=655)
    google_map_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address = EncryptedTextField(null=True,blank=True)
    status = models.CharField(max_length=120, default="Active")  # Active / Inactive
    starting_time = models.TimeField(null=True,blank=True)
    closing_time = models.TimeField(null=True,blank=True)
    phone = EncryptedCharField(max_length=120, blank=True, null=True)
    email = EncryptedEmailField(blank=True, null=True)
    company_id = EncryptedCharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name 


# shifts
# class ShiftTable(models.Model):
#     shifts_name = models.CharField(max_length=200)
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return self.shifts_name
class ShiftTable(models.Model):
    shifts_name = models.CharField(max_length=200)

   

    # Relaxation Time (Punch-in relaxation)
    relaxation_start = models.TimeField(null=True, blank=True)
    relaxation_end = models.TimeField(null=True, blank=True)

    # Break Time
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    # Lunch Time
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)

    # Evening Break
    evening_break_start = models.TimeField(null=True, blank=True)
    evening_break_end = models.TimeField(null=True, blank=True)


    punch_out_time = models.TimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.shifts_name



class EmployeeGoogleFormResponse(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    father_or_mother_number = models.CharField(max_length=20, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    place = models.CharField(max_length=255, null=True, blank=True)
    job_position = models.CharField(max_length=255, null=True, blank=True)
    
    # *CORRECTION: File Fields changed to CharField to store the URL string*
    # The Apps Script sends a URL string, not a file object.
    # CharField is suitable for storing the Google Drive link.
    adhar_card = models.CharField(max_length=500, null=True, blank=True) 
    passport_size_photo = models.CharField(max_length=500, null=True, blank=True)
    bank_passbook = models.CharField(max_length=500, null=True, blank=True)
    pan_card = models.CharField(max_length=500, null=True, blank=True)
    resume = models.CharField(max_length=500, null=True, blank=True)
    qualification_documents = models.CharField(max_length=500, null=True, blank=True) 
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.full_name


# ---------------------------
# Employee Detail
# ---------------------------
class EmployeeDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    first_name = EncryptedCharField(max_length=600)
    company_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    last_name = EncryptedCharField(max_length=600)
    employee_id = EncryptedCharField(max_length=250, unique=True, db_index=True)
    department = EncryptedCharField(max_length=600, blank=True, null=True)
    designation = EncryptedCharField(max_length=600, blank=True, null=True)
    reporting_manager = EncryptedCharField(max_length=600, blank=True, null=True)      
    is_team_lead = models.BooleanField(default=False)
    salary = models.DecimalField(max_digits=100, decimal_places=2, blank=True, null=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True, null=True)
    phone = EncryptedCharField(max_length=120, blank=True, null=True)
    address = EncryptedCharField(max_length=655, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = EncryptedCharField(max_length=120, blank=True, null=True)
    nationality = EncryptedCharField(max_length=150, blank=True, null=True)
    blood_group = EncryptedCharField(max_length=100, blank=True, null=True)
    emergency_contact = EncryptedCharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_type = models.CharField(max_length=600, blank=True, null=True)
    job_type = models.CharField(max_length=600, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    face_encoding = models.JSONField(blank=True, null=True)
    emp_status = models.CharField(max_length=600, blank=True, null=True)
    emp_exit_date = models.DateField(blank=True, null=True)  
    removing_reason = EncryptedTextField(blank=True, null=True)
    employee_shift = models.ForeignKey(ShiftTable, on_delete=models.SET_NULL, null=True, blank=True)
    basic_earnings = EncryptedCharField(max_length=120, blank=True, null=True)
    pf_deduction = EncryptedCharField(max_length=120, blank=True, null=True)
    employee_state_insurance = EncryptedCharField(max_length=120, blank=True, null=True)
    income_tax = EncryptedCharField(max_length=120, blank=True, null=True)
    proffessional_tax = EncryptedCharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"


# BVC ---------------------------
# OTP Verification (Email OTP)
# ---------------------------
class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_hash = models.CharField(max_length=655,null=True,blank=True)
    purpose = models.CharField(max_length=150, default="login",null=True,blank=True)  
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  
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
    status = models.CharField(max_length=20, default="Success")  

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
    is_half_day = models.BooleanField(default=False)
    attendance_type = models.CharField(max_length=20)  # office / wfh
    location = models.CharField(max_length=255, blank=True, null=True)
    qr_scan = models.BooleanField(default=False)
    qrsession = models.ForeignKey("QR_Session", on_delete=models.SET_NULL, null=True, blank=True)  # ✅ fixed
    in_selfie = models.ImageField(upload_to="attendance_selfies/in", blank=True, null=True)
    out_selfie = models.ImageField(upload_to="attendance_selfies/out/", blank=True, null=True) # ✅ punch-out selfie
    status = models.CharField(max_length=20)  # Present / Absent
    punchout_status  = models.CharField(max_length=20,null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="verified_attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    punch_in = models.BooleanField(default=False)
    # half_time = models.CharField(null=True , blank=True)
    shifts = models.CharField(max_length=100, null=True , blank=True)


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
    status = models.CharField(max_length=20, default="Pending")  
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approved_leaves")
    attachments = models.FileField(upload_to="leave_attachments/", blank=True, null=True)
    reason = EncryptedTextField(blank=True, null=True)
    rejection_reason = EncryptedTextField(blank=True , null=True)
    is_team_lead_approved = models.BooleanField(default=False)
    is_project_leader_approved = models.BooleanField(default=False)
    is_hr_approved = models.BooleanField(default=False)
    is_ceo_approved = models.BooleanField(default=False)
    is_team_lead_rejected = models.BooleanField(default=False)
    is_project_leader_rejected = models.BooleanField(default=False)
    is_hr_rejected = models.BooleanField(default=False)
    is_ceo_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.status})"



# ---------------------------
# Holiday
# ---------------------------
class Holiday(models.Model):
    description = EncryptedCharField(max_length=500)
    date = models.DateField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)  

    def save(self, *args, **kwargs):
     
        if not self.type:
            self.type = 'Company Holiday' if self.added_by else 'Public Holiday'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} on {self.date} ({self.type})"    


# Project 
class Project(models.Model):
    project_logo = EncryptedImageField(upload_to="project_logo/",max_length=400)
    project_name =EncryptedCharField(max_length=600)
    client = EncryptedCharField(max_length=600)
    start_date = models.DateField()
    end_date = models.DateField()
    priority = EncryptedCharField(600)
    project_value = EncryptedCharField(600,null=True , blank =True)
    total_working_hours = EncryptedCharField(max_length=550)
    extra_time = EncryptedCharField(max_length=360,null=True , blank =True)
    status =    models.CharField(max_length=350, default="Pending")  # Pending / In Progress / Completed
    description = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now_add=True,null=True)
    attachment = EncryptedFileField(upload_to="Project_attachment/",max_length=500)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="project_assigned")
    reason_for_rejection = EncryptedTextField(null=True,blank=True)

    def __str__(self):
        return self.project_name


# project members
class ProjectMembers(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    team_leader = models.JSONField(null=True,blank=True)
    project_manager = models.JSONField(null=True,blank=True)
    tags = models.JSONField(null=True,blank=True)

    def __str__(self):
        return self.project.project_name


# ---------------------------
# Task
# ---------------------------
class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    title = EncryptedCharField(max_length=600)
    description = EncryptedTextField()
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="tasks_assigned")
    assigned_to = models.ManyToManyField(User, related_name="tasks_received", blank=True)
    status = models.CharField(max_length=150, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    priority = EncryptedCharField(max_length=550, default="Medium")  
    attachments = models.FileField(upload_to="task_attachments/", blank=True, null=True)
    total_working_hours = EncryptedCharField(max_length=650, null=True, blank=True)
    extra_time = EncryptedCharField(max_length=660, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"



# project images---------------------------------------------------------
class ProjectImages(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="images")
    image = EncryptedImageField(upload_to="project_images/",max_length=700)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.project.project_name}"

# project files---------------------------------------------------------
class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="files")
    file = EncryptedFileField(upload_to="project_files/",max_length=700)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.file.name}"
# ---------------------------
# NotificationLog
# ---------------------------
class NotificationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100,null=True,blank=True)
    action = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email} at {self.timestamp}"

# ---------------------------
# BankDetail
# ---------------------------
class BankDetail(models.Model):
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100,null=True,blank=True)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=150)
    documents = models.FileField(upload_to="bank_docs/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bank Detail for {self.employee.first_name} {self.employee.last_name}"



# salary history 

class SalaryComponent(models.Model):
 

    component_type = models.CharField(max_length=20, )
    title = models.CharField(max_length=100)
    rate_type = models.CharField(max_length=20, )
    rate_value = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    description = models.TextField(null=True, blank=True)

    employee_contribution = models.CharField(max_length=255, null=True, blank=True)
    employer_contribution = models.CharField(max_length=255, null=True, blank=True)

    example_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.component_type})"
    
    
class SalaryHistory(models.Model):
    employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
    salary_component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.CASCADE,
        related_name="components",null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    pdf_file = models.FileField(upload_to="salary_pdfs/",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    effective_date = models.DateField(null=True,blank=True)

    def __str__(self):
        return f"Salary History for {self.employee.first_name} {self.employee.last_name} - {self.amount}"
    



# ---------------------------
# SalaryHistory
# ---------------------------
# class SalaryHistory(models.Model):
#     employee = models.ForeignKey(EmployeeDetail, on_delete=models.CASCADE)
#     amount = EncryptedDecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
#     pdf_file = models.FileField(upload_to="salary_pdfs/",null=True,blank=True)
#     created_at = models.DateTimeField(auto_now=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     effective_date = models.DateField(null=True,blank=True)

#     def __str__(self):
#         return f"Salary History for {self.employee.first_name} {self.employee.last_name} - {self.amount}"


#---------------------------
# department

class Department(models.Model):
    name = EncryptedCharField(max_length=600)
    description = EncryptedTextField(null=True,blank=True)
    # department_head = models.CharField(max_length=100, null=True,blank=True)
    department_head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        # Only users with 'admin' role can be department heads
    )

    def __str__(self):
        return self.name

#---------------------------    
# designation
class Designation(models.Model):
    title = EncryptedCharField(max_length=700)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="designations")
    description = EncryptedTextField(null=True,blank=True)

    def __str__(self):
        return self.title    
    


# terms and conditions
class TermsAndConditions(models.Model):
    title = EncryptedCharField(max_length=700, default="Terms and Conditions")
    content = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Terms and Conditions (Last updated: {self.updated_at})"
    

    #  privacy policy
class PrivacyPolicy(models.Model):
    title = EncryptedCharField(max_length=700, default="Privacy Policy")
    content = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Privacy Policy (Last updated: {self.updated_at})"
    
#   about us
class AboutUs(models.Model):
    title = EncryptedCharField(max_length=700, default="About Us")
    content = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"About Us (Last updated: {self.updated_at})"  



class Worksheet(models.Model):
    title = EncryptedCharField(max_length=755, blank=False)
    file = models.FileField(upload_to="worksheets/")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Encrypt size also
    file_size = EncryptedCharField(max_length=500, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Save file size encrypted
        if self.file and not self.file_size:
            size_mb = round(self.file.size / (1024 * 1024), 2)
            self.file_size = f"{size_mb} MB"
            super().save(update_fields=["file_size"])

    def __str__(self):
        return self.title
    
    
class Notice(models.Model):
    title = EncryptedCharField(max_length=255)
    date = models.DateField(null=True, blank=True)  
    department = EncryptedCharField(max_length=150)
    description = EncryptedTextField()
    is_pinned = models.BooleanField(default=False)   
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # 23 tables


class TrainingVideo(models.Model):
    title = EncryptedCharField(max_length=255)
    description = EncryptedTextField(blank=True)

    video_file = models.FileField(upload_to="training_videos/")
    duration = EncryptedCharField(max_length=20, blank=True)

    views = models.PositiveIntegerField(default=0)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    


# polls and feedback section 
class Form(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class Question(models.Model):

    QUESTION_TYPES = (
        ('text', 'Text'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('dropdown', 'Dropdown'),
    )

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)

    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.option_text

class Shiftaddon(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    team = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_schedules'
    )

    def __str__(self):
        return f"{self.team.name if self.team else 'No Team'} Shift"