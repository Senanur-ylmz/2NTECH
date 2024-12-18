# Generated by Django 4.2.5 on 2024-11-25 22:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('no_of_leaves', models.FloatField(default=0)),
                ('no_of_remaining_leaves', models.FloatField(default=15)),
                ('no_of_applied_leaves', models.FloatField(default=0)),
                ('total_no_of_leaves', models.FloatField(default=15)),
            ],
        ),
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_leaves', models.PositiveIntegerField(default=15)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Date')),
                ('leave_type', models.CharField(choices=[('Casual Leave', 'Casual Leave'), ('Sick Leave', 'Sick Leave')], default='Casual Leave', max_length=20)),
                ('duration', models.CharField(choices=[('FULL Day', 'Full Day'), ('Half Day', 'Half Day')], default='Full Day', max_length=20)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(choices=[('Waiting', 'Waiting'), ('Not Approved', 'Not Approved'), ('Approved', 'Approved')], default='Not Approved', max_length=20)),
                ('employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee', to='app.employeedetails')),
            ],
        ),
    ]
