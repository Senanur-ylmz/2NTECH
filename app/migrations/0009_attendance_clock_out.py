# Generated by Django 5.1.3 on 2024-11-26 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_remove_attendance_date_attendance_clock_in_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='clock_out',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
