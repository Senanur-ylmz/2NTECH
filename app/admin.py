# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import *

# Register your models here.

class LeaveApplicationAdmin(admin.ModelAdmin):
	list_display = ['employee', 'date','leave_type','duration','status']
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'clock_in', 'clock_out', 'status']
    list_filter = ['employee', 'status']
    search_fields = ['employee__name']
admin.site.register(Leave)
admin.site.register(EmployeeDetails)
admin.site.register(LeaveApplication, LeaveApplicationAdmin)
admin.site.register(Attendance, AttendanceAdmin)
from django.contrib import admin
from .models import Notification

admin.site.register(Notification)