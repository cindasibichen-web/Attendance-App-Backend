from celery import shared_task
from django.utils import timezone
from datetime import date, time
from django.db.models import Q
from . models import *
import calendar
from  django.core.mail import send_mail
from django.conf import settings
@shared_task
def send_missed_punch_in_notifications():
    """
    Celery task that sends notifications to all employees
    who haven't punched in by 9:30 AM.
    """
    now = timezone.now()
    today = date.today()

    # Get all active employees
    employees = EmployeeDetail.objects.filter(user__is_active=True)

    # Get all employees who already punched in
    present_employees = Attendance.objects.filter(
        date=today, punch_in=True
    ).values_list("employee_id", flat=True)

    #Get employees who haven't punched in yet
    missing_employees = employees.exclude(id__in=present_employees)

    #Skip if current time is before 9:30 AM
    # if now.time() < time(9, 55):
    #     print("It's not yet 9:30 AM. Task skipped.")
    #     return

    #Create NotificationLog entries
    notifications = []
    for emp in missing_employees:
        if hasattr(emp, "user"):
            notifications.append(NotificationLog(
                user=emp.user,
                title="Missed Punch In",
                action="You have missed your punch-in for today.",
                is_active=True
            ))

    NotificationLog.objects.bulk_create(notifications)
    print(f"{len(notifications)} missed punch-in notifications created.")


# task for saving the attendance based on absent employees
@shared_task
def auto_mark_absent():
    today = date.today()

    #  Skip Sunday only (make Saturday a working day)
    # calendar.weekday(...) returns 0=Mon .. 6=Sun
    if calendar.weekday(today.year, today.month, today.day) == 6:
        print("Sunday — skipping absent marking.")
        return

    employees = EmployeeDetail.objects.all()
    count_absent = 0

    for emp in employees:
     
        if not Attendance.objects.filter(employee=emp, date=today).exists():
            Attendance.objects.create(
                employee=emp,
                date=today,
                status="Absent",
                attendance_type="office",
                punch_in=False,
                qr_scan=False,
            )
            count_absent += 1

    print(f"{count_absent} employees marked as Absent for {today}.")


#   want to send warning mail to the employees 

@shared_task
def warning_mail_for_project_deadlines():
    """
    Celery task that sends warning emails for:
    1. Projects nearing their deadlines.
    2. Tasks (inside those projects) nearing their due dates.
    """

    today = date.today()
    warning_period = timedelta(days=3)
    warning_date = today + warning_period

    # 1️⃣ Find projects whose end_date is within 3 days
    projects_near_deadline = Project.objects.filter(
        end_date__lte=warning_date,
        end_date__gte=today
    )

    for project in projects_near_deadline:
        # --------------------------------
        # Send project warning email
        # --------------------------------
        subject = f"Project Deadline Approaching: {project.project_name}"
        message = (
            f"Dear Team,\n\n"
            f"The project '{project.project_name}' is nearing its deadline on {project.end_date}.\n"
            f"Please review the pending tasks and take necessary actions.\n\n"
            f"Regards,\nProject Management Team"
        )

        # Collect emails of project manager, team leader, and assigned_by
        recipient_list = []

        try:
            members = ProjectMembers.objects.get(project=project)
            # project_manager and team_leader are JSON fields (likely containing dicts or lists)
            if isinstance(members.project_manager, list):
                recipient_list.extend([m.get("email") for m in members.project_manager if m.get("email")])
            elif isinstance(members.project_manager, dict):
                recipient_list.append(members.project_manager.get("email"))

            if isinstance(members.team_leader, list):
                recipient_list.extend([t.get("email") for t in members.team_leader if t.get("email")])
            elif isinstance(members.team_leader, dict):
                recipient_list.append(members.team_leader.get("email"))
        except ProjectMembers.DoesNotExist:
            pass

        if project.assigned_by and project.assigned_by.email:
            recipient_list.append(project.assigned_by.email)

        recipient_list = list(set(recipient_list))  # Remove duplicates

        if recipient_list:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True
            )
            print(f"Sent project deadline warning for '{project.project_name}' to {recipient_list}")

        # --------------------------------
        # Send task warning emails
        # --------------------------------
        tasks_near_due = Task.objects.filter(
            project=project,
            due_date__lte=warning_date,
            due_date__gte=today
        )

        for task in tasks_near_due:
            task_recipients = [user.email for user in task.assigned_to.all() if user.email]

            if task_recipients:
                task_subject = f"Task Deadline Approaching: {task.title}"
                task_message = (
                    f"Dear Team Member,\n\n"
                    f"The task '{task.title}' under project '{project.project_name}' "
                    f"is nearing its due date on {task.due_date}.\n"
                    f"Please complete it on priority.\n\n"
                    f"Regards,\nProject Management Team"
                )
                send_mail(
                    subject=task_subject,
                    message=task_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=task_recipients,
                    fail_silently=True
                )
                print(f"Sent task deadline warning for '{task.title}' to {task_recipients}")

    print("All warning emails processed successfully.")



# tasks for missed punch out notification 
@shared_task
def send_missed_punch_out_notifications():
    """
    Celery task that sends notifications to all employees
    who have punched in but not punched out for the current day.
    """
    today = date.today()

    # 🔹 Find all active employees who have punched in but not punched out today
    employees_to_notify = EmployeeDetail.objects.filter(
        user__is_active=True,
        id__in=Attendance.objects.filter(
            date=today,
            out_time__isnull=True
        ).values_list('employee_id', flat=True)
    )

    notifications = []

    for emp in employees_to_notify:
        if hasattr(emp, "user"):
 
            already_notified = NotificationLog.objects.filter(
                user=emp.user,
                title="Missed Punch Out",
                timestamp__date=today 
            ).exists()

            if not already_notified:
                notifications.append(NotificationLog(
                    user=emp.user,
                    title="Missed Punch Out",
                    action="You have missed your punch-out for today. Please contact HR.",
                    is_active=True
                ))

    if notifications:
        NotificationLog.objects.bulk_create(notifications)
        print(f"{len(notifications)} missed punch-out notifications created.")
    else:
        print("No missed punch-out notifications created today.")