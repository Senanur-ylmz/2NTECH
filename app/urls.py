from django.urls import path, include
from .views import *
from .views import company_info
from .views import record_entry_time
from . import views


urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('employee/<int:pk>/', Home.as_view(), name='home'),
    path('login/', Login.as_view(), name='login'),
    path('admin-login/', AdminLogin.as_view(), name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('super-admin/', SuperAdmin.as_view(), name='super-admin'),
        # Lateness records
    path('lateness-records/', views.lateness_records_view, name='lateness_records'),

    # Login/logout times
    path('login-logout-times/', views.login_logout_times_view, name='login_logout_times'),

    # Leave applications
    path('leave-applications/', views.leave_applications_view, name='leave_applications'),
    
    # Mark notification as read
    path('mark-notification-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),

    # Get notifications
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('save-leave-status/<int:pk>/', SaveLeaveStatus.as_view(), name='save-leave-status'),
    path('delete-leave-application/<int:pk>/', DeleteLeaveApplication.as_view(), name='delete-leave-application'),
    path('api/company_info/', company_info, name='company_info'),
    path('record-entry-time/', record_entry_time, name='record-entry-time'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('mark-notification-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('api/employee/<int:user_id>/monthly-working-hours/', views.get_monthly_working_hours, name='get_monthly_working_hours'),
    path('save-leave-status/', save_leave_status, name='save_leave_status'),
    path('working-hours/<int:user_id>/', views.get_monthly_working_hours, name='monthly_working_hours'),
    path('monthly-working-hours/', views.monthly_working_hours_view, name='monthly_working_hours'),
    path('generate-monthly-report/', views.generate_monthly_report, name='generate_monthly_report'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('apply-leave/', ApplyLeaveView.as_view(), name='apply_leave'),
    path('api_apply_leave/', ApplyLeave.as_view(), name='api_apply_leave'),
    path('leave-list/', LeaveListView.as_view(), name='leave_list'),
    path('update-employee-leaves/', update_employee_leaves, name='update_employee_leaves'),
]