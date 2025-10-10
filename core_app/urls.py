from django.urls import path
from . views import *

urlpatterns = [
    # Auth & Login
    path('login/', LoginView.as_view(), name='login'),
    path('refresh-token/',RefreshTokenView.as_view(),name='refresh-token'),
    path('check-login/', CheckLoginView.as_view(), name='check-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # User
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('employee-profile-details/', EmployeeProfileView.as_view(), name='employee-profile-details'),
    path('notifications/', NotificationStatusView.as_view(), name='notifications'),

    # Employee
    path('employees/register/', EmployeeRegistrationView.as_view(), name='employee-register'),

    path('qr-session/', QRSessionCreateAPIView.as_view(), name='qr-session'),

    path('face-verify/',FaceVerifyView.as_view(), name='face-verify'),
    path('face-logout/',FaceLogoutView.as_view(), name='face-logout'),


    path("punch-in/", punch_in_view, name="punch_in"),
    path('employee-attendance/', EmployeeAttendanceView.as_view(), name='employee-attendance'),
    path('daily-punch-summary/', DailyPunchSessionSummaryView.as_view(), name='daily-punch-summary'),
    path('employee-all-attendance-details/', EmployeeAllAttendanceDetailsView.as_view(), name='employee-all-attendance-details'),
    path("punch-out/", punch_out, name="punch_out"),

    path('overview-counts-api/', EmployeePresenceAbsenceLeaveCountView.as_view(), name='overview-counts-api'),
    path('leave-applying/', LeaveApplyingView.as_view(), name='leave-applying'),

    path('dashboard-leave-counts/',DashboardLeaveDetailsCountAPI.as_view(),name='dashboard-leave-counts'),

    path('leavesview/', LeaveListView.as_view(), name='leave-list'),

    path('attendance-report/', AttendanceReportView.as_view(), name='attendance-report'),
   
    # Tasks
    path('employee-tasks/', EmployeeTasksWithProjectAPI.as_view(), name='employee-tasks'),
    path('list-holidays/', HolidayListView.as_view(), name='list-holidays'),

    path('notification-list/',NotificationStatusView.as_view(),name='notification-list'),
    path('delete-notification/<int:notification_id>/',NotificationDeleteView.as_view(),name='delete-notification'),
    path('undo-notification/<int:notification_id>/',UndoNotificationDeleteView.as_view(),name='undo-notification'),


    path("logout/", LogoutView.as_view(), name="logout"),

]