from django.urls import path
from .views import *

urlpatterns = [
    
path('adminprofile/', AdminProfileView.as_view(), name='admin-profile'),
path('all-employee-list/',EmployeeListAPI.as_view(),name='all-employee-list'),
path('pending-approval-count/',DashboardPendingApprovalsCountView.as_view(),name='pending-approval-count'),
path('taskpercentage/', TaskPercentageAPIView.as_view(), name='task-percentage'),
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
path('employee/', EmployeeListAPIView.as_view(), name='employee-list'),
path('list-all-leaves/',LeaveListAPIView.as_view(),name='list-all-leaves'),
path('leave-accept/', LeaveAcceptAPI.as_view(), name='leave-accept'),
path('leave-reject/', LeaveRejectAPI.as_view(), name='leave-reject'),

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



path('employee-remove/', RemoveEmployeeAPIView.as_view(), name='employee-remove'),
path('employee-reactivate/', ReactivateEmployeeAPIView.as_view(), name='employee-reactivate'),

path('inactive-employees-list/',InactiveEmployeeListAPIView.as_view(),name='inactive-employees-list'),
path('active-employees-list/',ActiveEmployeeListAPIView.as_view(),name='active-employees-list'),


path('create-department/', DepartmentCreateView.as_view(), name='create-department'),
path('list-departments/',DepartmentListView.as_view(),name='list-departments'),
path('create-designation/', DesignationCreateView.as_view(), name='create-designation'),
path('list-designations/',DesignationListView.as_view(),name='list-designations'),
path('notificationsuser/<int:user_id>/', NotificationLogByUserAPIView.as_view(), name='user-notifications'),
path('update-notificationlog/<int:pk>/', NotificationLogEditAPIView.as_view(), name='update-notificationlog'),
path('birthdaystoday/', TodayBirthdayAPIView.as_view(), name='birthdays-today'),
path('birthdaystomorrow/', TomorrowBirthdayAPIView.as_view(), name='birthdays-tomorrow'),
path('birthdaysupcoming/', UpcomingBirthdayAPIView.as_view(), name='birthdays-upcoming'),

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

]