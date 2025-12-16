# from celery import shared_task
# from fcm_django.models import FCMDevice
# from django.core.exceptions import ObjectDoesNotExist

# @shared_task
# def send_push_notification_task(user_id, title, message, data_payload=None):
#     """
#     Asynchronous task to send a push notification to a user's devices.
#     """
#     try:
#         # Find devices for the given user_id
#         devices = FCMDevice.objects.filter(user_id=user_id, active=True)
#         if devices.exists():
#             # The send_message method handles sending to multiple devices
#             devices.send_message(
#                 title=title,
#                 body=message,
#                 data=data_payload or {}
#             )
#             return f"Successfully sent push notification to user {user_id}."
#     except ObjectDoesNotExist:
#         return f"User with id {user_id} not found."
#     except Exception as e:
#         # It's good practice to log the exception
#         print(f"Failed to send push notification to user {user_id}: {e}")
#         return f"Error sending push notification: {e}"
