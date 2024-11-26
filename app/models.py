# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
# models.py
from django.db import models
from django.contrib.auth.models import User

class EmployeeDetails(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=True)
    no_of_leaves = models.FloatField(default=0)
    no_of_remaining_leaves = models.FloatField(default=15)
    no_of_applied_leaves = models.FloatField(default=0)
    total_no_of_leaves = models.FloatField(default=15)
    is_new_user = models.BooleanField(default=True)  # Yeni kullanıcı işareti

    def __str__(self):
        return str(self.name)



class Attendance(models.Model):
    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name="attendances")
    clock_in = models.DateTimeField(default=timezone.now)
    clock_out = models.DateTimeField(null=True, blank=True)  # New field for logout time
    status = models.CharField(max_length=50, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')

    def __str__(self):
        return f"{self.employee.name} - {self.clock_in.date()} - {self.status}"


class Leave(models.Model):
    total_leaves = models.PositiveIntegerField(default=15)

    def __str__(self):
        return str(self.total_leaves)


class LeaveApplication(models.Model):
    STATUS = [
        ("Waiting", 'Waiting'),
        ("Not Approved", 'Not Approved'),
        ("Approved", "Approved"),
    ]

    LEAVE_TYPE = [
        ("Casual Leave", 'Casual Leave'),
        ("Sick Leave", "Sick Leave"),
    ]

    DURATION = [
        ("Full Day", 'Full Day'),
        ("Half Day", "Half Day"),
    ]

    date = models.DateField('Date', null=True, blank=True)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE, default='Casual Leave')
    duration = models.CharField(max_length=20, choices=DURATION, default='Full Day')
    employee = models.ForeignKey(EmployeeDetails, related_name='leave_applications', on_delete=models.CASCADE, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Waiting')

    def __str__(self):
        return f"{self.leave_type} - {self.duration} on {self.date}"

class LatenessRecord(models.Model):
    employee = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    lateness_minutes = models.PositiveIntegerField(default=0)  # Gecikme süresi (dakika)
    notification_sent = models.BooleanField(default=False)  # Bildirim gönderildi mi?

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.lateness_minutes} minutes"


# models.py
from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username if self.user else 'Unknown'}: {self.message}"

