# Generated by Django 5.1.3 on 2024-11-26 14:43

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_attendance_clock_out'),
    ]

    operations = [
        migrations.CreateModel(
            name='LatenessRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('lateness_minutes', models.PositiveIntegerField(default=0)),
                ('notification_sent', models.BooleanField(default=False)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.employeedetails')),
            ],
        ),
    ]
