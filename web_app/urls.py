from django.urls import path
from web_app.views.admin_profile_views import *
from web_app.views.attendance_views  import *
from web_app.views.employees_views import *
from web_app.views.leave_views import *
from web_app.views.project_views import *
from web_app.views.worksheet_views import *
from web_app.views.notice_views import *
from web_app.views.privacy_noti_views import *


urlpatterns = [

    path('admin-email/', AdminEmailView.as_view(), name='admin-email'),
    
    path('admin-punch-in/',AdminPunchInAPIView.as_view(),name='admin-puch-in'),
    path('admin-punch-out/',AdminPunchOutAPIView.as_view(),name='admin-punch-out'),

path('adminprofile/', AdminProfileView.as_view(), name='admin-profile'),
path('edit-profile/',AdminEditProfile.as_view(),name='edit-profile'),

path('create-shift/', ShiftCreateView.as_view(), name='create-shift'),
path('list-shifts/',ShiftListView.as_view(),name='list-shifts'),
path('update-shift/<int:pk>/', ShiftEditView.as_view(), name='update-shift'),
# path('delete-shift/<int:pk>/', ShiftDeleteView.as_view(), name='delete-shift'),

path('shift-delete/<int:id>/', ShiftDeleteAPIView.as_view(), name='shift-delete'),
   
path('all-employee-list/',EmployeeListAPI.as_view(),name='all-employee-list'),
path('pending-approval-count/',DashboardPendingApprovalsCountView.as_view(),name='pending-approval-count'),
path('taskpercentage/', TaskPercentageAPIView.as_view(), name='task-percentage'),
path('taskhours/', TodaysTaskHoursAPIView.as_view(), name='task-hours'),
path('add-project/',AddProjectApi.as_view(),name='add-project'),
path('update-project/<int:pk>/',UpdateProjectApi.as_view(),name='update-project'),
path("projectsdelete/<int:project_id>/", DeleteProjectApi.as_view(), name="delete-project"),
path('project-details-by-id/<int:project_id>/', ProjectDetailByIDAPIView.as_view(), name='project-details-by-id'),
path('add-list-project-image/',ProjectImageUploadApi.as_view(),name='add-project-image'),
path('add-list-project-image/<int:project_id>/',ProjectImageUploadApi.as_view(),name='add-list-project-image'),
path('delete-update-project-image/<int:image_id>/',ProjectImageDeleteUpdateApi.as_view(),name='delete-update-project-image'),
path('projectfile/', ProjectFileListCreateAPIView.as_view(), name='project-file'),
path('project-filesview/<int:project_id>/', ProjectFileRetrieveAPIView.as_view(), name='project-file-detail'),
path('project-filesupdate/<int:id>/', ProjectFileUpdateAPIView.as_view(), name='project-file-update'),
path('projectfiledelete/<int:id>/', ProjectFileDeleteAPIView.as_view(), name='projectfile-delete'),
path('list-all-projects/',ListProjectsApi.as_view(),name='list-all-projects'),

path('new-list-projects/', NewListProjectsApi.as_view(), name='new-list-projects'),

path('list-all-tasks/',TaskListAPIView.as_view(),name='list-all-tasks'),
path('add-tasks-to-project/',AddTasksToProjectApi.as_view(),name='add-tasks-to-project'),
path('update-task/<int:task_id>/',EditTaskApi.as_view(),name='update-task'),
path('delete-task/<int:task_id>/',DeleteTaskApi.as_view(),name='delete-task'),
path('projects-accept/', AcceptProjectAPIView.as_view(), name='projects-accept'),
path('projects-reject/', RejectProjectAPIView.as_view(), name='projects-reject'),
path('project-tasks-count/',ProjectTaskCountAPIView.as_view(),name='project-tasks-count'),
path('employee-project-task-by-empid/<int:employee_id>/',EmployeeIdProjectsTasksAPIView.as_view(),name='employee-project-task-by-empid'),
path('teamleaders/', TeamLeaderListAPIView.as_view(), name='teamleader-list'),
path('projectmanager/', ProjectmanagerListAPIView.as_view(), name='projectmanager-list'),
path('projectmemberslist/<int:employee_id>/', ProjectMembersListAPIView.as_view(), name='projectmemberslist'),
path('employee/', EmployeeListAPIView.as_view(), name='employee-list'),
path('list-all-leaves/',LeaveListAPIView.as_view(),name='list-all-leaves'),
path('leave-accept/', LeaveAcceptAPI.as_view(), name='leave-accept'),
path('leave-reject/', LeaveRejectAPI.as_view(), name='leave-reject'),

path('active-emp-count/',ActiveEmployeeCountView.as_view(),name='active-emp-count'),


path('leavediagram/<int:employee_id>/', LeavediagramAPIView.as_view(), name='leavediagram'),

path("attendance-summary/", AttendanceSummaryView.as_view(), name="attendance-summary"),
path("employeesadminview/", EmployeeListadminView.as_view(), name="employee-listadminview"),
path('employee-designation-counts/',EmployeeCountByDesignation.as_view(),name='employee-designation-counts'),
path('todays-employee-count-by-designation/',TodayEmployeeCountByDesignation.as_view(),name='todays-employee-count-by-designation'),
path('todays-attendance-count/',TodaysAttendanceCount.as_view(),name='todays-attendance-count'),

path("employeesfilter-by-designation/", EmployeeListAdminFilteredView.as_view(), name="employeesfilter-by-designation"),
path('todays-all-employess-attendance/',AllTodaysEmployeeCheckinCheckOutDetails.as_view(),name='todays-all-employess-attendance'),
path("employeesdetails/<int:employee_id>/", EmployeeAttendanceView.as_view(), name="employee-attendance"),
path("employeesdetailspast7days/<int:employee_id>/", EmployeeAttendanceViewpast7days.as_view(), name="employee-attendancepast7days"),
path('employee-att-details-by-date-range/',AttendanceByDateRangeView.as_view(),name='employee-att-details-by-date-range'),
path('filter-emp-attendance-by-status/<int:employee_id>/',EmployeeAttendanceFilterByStatusView.as_view(),name='filter-emp-attendance-by-status'),
path("attendanceedit/<int:pk>/", AttendanceEditView.as_view(), name="attendance-update"),
path("holidayscreate/", HolidayCreateView.as_view(), name="holiday-create"),

path("employee-detail-with-leave/<int:pk>/", EmployeeDetailWithLeave.as_view(), name="employee-detail-with-leave"),
path("employeedetailedit/<int:pk>/", EmployeeDetailEdit.as_view(), name="employeeedit"),

path('employee-remove/', RemoveEmployeeAPIView.as_view(), name='employee-remove'),
path('employee-reactivate/', ReactivateEmployeeAPIView.as_view(), name='employee-reactivate'),

path('inactive-employees-list/',InactiveEmployeeListAPIView.as_view(),name='inactive-employees-list'),
path('active-employees-list/',ActiveEmployeeListAPIView.as_view(),name='active-employees-list'),

path('search-inactive-employees/',InactiveEmployeeSearchAPIView.as_view(),name='search-inactive'),
path("active-employee-search/", ActiveEmployeeSearchListAPIView.as_view(), name="active-employee-search"),

path('create-department/', DepartmentCreateView.as_view(), name='create-department'),
path("ceo-cmo-search/", CeocmoSearchListAPIView.as_view(), name="ceo-cmo-search"),
path('list-departments/',DepartmentListView.as_view(),name='list-departments'),
path('create-designation/', DesignationCreateView.as_view(), name='create-designation'),
path('list-designations/',DesignationListView.as_view(),name='list-designations'),
path('list-designation-by-department/<int:department_id>/',DesignationListByDepartmentAPIView.as_view(),name='list-designation-by-department'),
path('notification-list-admin/',AdminNotificationListView.as_view(),name='notification-list-admin'),
path('delete-notification-admin/<int:notification_id>/',AdminNotificationDeleteView.as_view(),name='delete-notification-admin'),
path('notificationsuser/<int:user_id>/', NotificationLogByUserAPIView.as_view(), name='user-notifications'),
path('update-notificationlog/<int:pk>/', NotificationLogEditAPIView.as_view(), name='update-notificationlog'),
path('birthdaystoday/', TodayBirthdayAPIView.as_view(), name='birthdays-today'),
path('birthdaystomorrow/', TomorrowBirthdayAPIView.as_view(), name='birthdays-tomorrow'),
path('birthdaysupcoming/', UpcomingBirthdayAPIView.as_view(), name='birthdays-upcoming'),
# all birthdays together today , tomorow and upcoming
path('birthday-list-all/',BirthdayListAPIView.as_view(),name='birthday-list-all'),

path('birthdaystodaywish/', TodayBirthdaywishAPIView.as_view(), name='birthdays-todaywish'),
path('birthdaystodaywishid/<int:pk>/', TodayBirthdayWishidAPIView.as_view(), name='birthday-wish-by-id'),

path('admin-notification-list/', AdminNotificationLogListAPIView.as_view(), name='admin-notification-list'),
path('projectscount/', ProjectCountAPIView.as_view(), name='project-count'),
path('taskcount/', TaskCountAPIView.as_view(), name='task-count'),

path('taskslast-7-days/', Last7DaysTasksAPIView.as_view(), name='tasks-last-7-days'),
path("taskliststatusfilter/<str:status_filter>/", TaskStatusFilterAPIView.as_view(), name="task-status-filter"),
path('create-list-branch/', BranchCreateListView.as_view(), name='create-list-branch'),

path("employeesactivity/", EmployeeActivityListAPIView.as_view(), name="employeeActivity-list"),
path('last-7-days-employee-activity/', Last7DaysActivityListAPIView.as_view(), name='last-7-days-employee-activity'),
path('employee-work-hour-summary/<int:employee_id>/', EmployeeWorkHourSummaryAPI.as_view(), name='employee-work-hour-summary'),
path('leave-details-diagram/<int:id>/', LeaveDetailsDiagramView.as_view(), name='leave-details-diagram'),
path('employee-todays-working-hour/<int:employee_id>/',EmployeeDailyProductivity.as_view(), name='employee-todays-work-hour'),
# leave and attendance yearly stats for productivity dashboard
path('attendanceyearly/', AttendanceYearlyStatsAPIView.as_view(), name='attendance-yearly-current'),
    
    # Specific year
path('attendanceyearly/<int:year>/', AttendanceYearlyStatsAPIView.as_view(), name='attendance-yearly-stats'),
path('leavesyearly/<int:year>/', LeaveYearlyStatsAPIView.as_view(), name='leavesyearly'),
path('leavesyearly/', LeaveYearlyStatsAPIView.as_view(), name='leavesyearly'),

path('search-project-manager/',ProjectManagerSearchView.as_view() ,name='search-project-manager'),
path("team-leaders-search/", TeamLeaderSearchListAPIView.as_view(), name="team-leader-search-letter"),
path('search-employee/',EmployeeRoleSearchByNameAPIView.as_view(),name='search-employee'),
path('search-branch/',SearchBranchName.as_view(),name='search-branch'),

path('monthly-productivity-count/', MonthlyProductivityCount.as_view(), name='productivity-count'),

path("working-hoursallemp/", WorkingHoursallempView.as_view(), name="today-working-hours"),


path("add-worksheet/",WorksheetListCreateAPI.as_view(), name="add-worksheet"),
path("worksheet_list/",WorksheetAllListAPI.as_view(), name="worksheet_list"),
path("worksheetdelete/<int:pk>/",WorksheetDeleteAPI.as_view(),name="worksheetdelete"),
path("worksheet-update/<int:pk>/", WorksheetTitleUpdateAPI.as_view(), name="worksheet-update"),


path("view-shift-details/", get_all_shifts,name="view-shift-details"),

path("shift-delete/<int:pk>/", delete_shift, name="delete-shift"),
path('videos-upload/', TrainingVideoUploadAPIView.as_view(),name="videos-upload"),
path('videos-view/', TrainingVideoListAPIView.as_view(),name="videos-view"),
path("trainingvideo-update-delete/<int:pk>/",TrainingVideosEditDeletAPI.as_view(), name="trainingvideo-update-delete"),

path('create-view-notice/', NoticeListCreateAPI.as_view(), name="notice-list-create"),
path('notice-delete/<int:pk>/', NoticeDeleteAPI.as_view(), name="notice-delete"),
path('notice-update/<int:pk>/', NoticeUpdateAPI.as_view(), name="notice-update"),


#  feedback questions api 
path('add-feedback-questions/', FeedbackQuestionFormCreateAPIView.as_view() , name='add-feedback-questions'),
path('list-feedback-questions/', FeedbackQuestionFormCreateAPIView.as_view() , name='list-feedback-questions'),
path('update-feedbackback-questions/<int:pk>/', EditDeleteFeedbackQuestionFormAPIView.as_view() , name='update-feedback-questions'),
path("shift-addon/", ShiftaddonListCreate.as_view(), name="shift-addon-list-create"),
path("shift-addon-edit-delete/<int:pk>/", ShiftaddonEditDelete.as_view(), name="shift-addon-edit-delete"),

path('add-list-privacy-policy/',AddListPrivacyPolicyAPIView.as_view(),name='add-list-privacy-policy'),
path('privacy-policy-edit/<int:pk>/',PrivacyPolicyEditAPIView.as_view(),name='privacy-policy-edit'),

path('terms-and-conditions/', AddListTermsAndConditionsAPIView.as_view(), name='terms-and-conditions'),
path('terms-and-conditionsedit/<int:pk>/', TermsAndConditionsEditAPIView.as_view(), name='terms-and-conditions-edit'),
path('about-us-add-list/', AddListAboutUsAPIView.as_view(), name='about-us-add-list'),
path('about-usedit/<int:pk>/', AboutUsEditAPIView.as_view(), name='about-us-edit'),



]