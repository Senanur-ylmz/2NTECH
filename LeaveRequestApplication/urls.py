from django.contrib import admin
from django.urls import path, include  # Import path instead of url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),  # Use path here for including app's URLs
]
