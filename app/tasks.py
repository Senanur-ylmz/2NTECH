# tasks.py
from celery import shared_task
from .models import Notification
from django.contrib.auth.models import User

@shared_task
def send_periodic_notification():
    user = User.objects.get(id=1)  # Örneğin admin kullanıcısı
    message = "Yeni bir bildirim var!"
    Notification.objects.create(user=user, message=message)
