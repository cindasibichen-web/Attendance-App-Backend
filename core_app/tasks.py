from celery import shared_task
from django.utils import timezone
from datetime import date, time
from django.db.models import Q
from . models import *


@shared_task
def send_missed_punch_in_notifications():
    """
    Celery task that sends notifications to all employees
    who haven't punched in by 9:30 AM.
    """
    now = timezone.now()
    today = date.today()

    # 1️⃣ Get all active employees
    employees = EmployeeDetail.objects.filter(user__is_active=True)

    # 2️⃣ Get all employees who already punched in
    present_employees = Attendance.objects.filter(
        date=today, punch_in=True
    ).values_list("employee_id", flat=True)

    # 3️⃣ Get employees who haven't punched in yet
    missing_employees = employees.exclude(id__in=present_employees)

    # 4️⃣ Skip if current time is before 9:30 AM
    if now.time() < time(9, 30):
        print("⏳ It's not yet 9:30 AM. Task skipped.")
        return

    # 5️⃣ Create NotificationLog entries
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
    print(f"✅ {len(notifications)} missed punch-in notifications created.")
