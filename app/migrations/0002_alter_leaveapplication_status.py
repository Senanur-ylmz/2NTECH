# Generated by Django 4.2.5 on 2024-11-25 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaveapplication',
            name='status',
            field=models.CharField(choices=[('Waiting', 'Waiting'), ('Not Approved', 'Not Approved'), ('Approved', 'Approved')], default='Waiting', max_length=20),
        ),
    ]