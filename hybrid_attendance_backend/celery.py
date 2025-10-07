# project_name/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_attendance_backend.settings')

app = Celery('hybrid_attendance_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()



from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-missed-punch-in-notifications-everyday-930am': {
        'task': 'core_app.tasks.send_missed_punch_in_notifications',
        'schedule': crontab(hour=9, minute=30),
    },
}
