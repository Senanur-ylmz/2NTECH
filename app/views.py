from django.shortcuts import render
from django.views.generic import (
    TemplateView, 
    FormView, 
    RedirectView
)
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib import messages
from random import randint
from datetime import datetime, timedelta
import calendar
from .models import *
from django.shortcuts import render
from django.views.generic import FormView
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .tasks import send_periodic_notification  # Celery görevini içe aktar
from django.http import JsonResponse
from app.tasks import send_periodic_notification
from django.conf import settings
from .models import Attendance, Notification
from django.utils import timezone
from .models import EmployeeDetails, LeaveApplication, Leave  # Gerekli modelleri burada içe aktarın.
from .models import Attendance, Notification
from datetime import datetime, time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import send_periodic_notification
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.utils.timezone import now
import calendar
from .models import Attendance, EmployeeDetails


def check_if_working_time(current_time):
    work_start = settings.WORK_START_TIME
    work_end = settings.WORK_END_TIME

    # Geçerli saatin iş saatleri içinde olup olmadığını kontrol et
    if work_start <= current_time <= work_end:
        return True
    return False

def check_if_holiday(day_name):
    if day_name in settings.HOLIDAY_DAYS:
        return True
    return False

def company_info(request):
    data = {
        "start_time": settings.COMPANY_START_TIME,
        "end_time": settings.COMPANY_END_TIME,
        "weekend_days": settings.WEEKEND_DAYS,
    }
    return JsonResponse(data)

def check_lateness(self, user):
    # Sabah 08:00 sabah saatini oluşturuyoruz
    start_time = datetime.combine(timezone.now().date(), time(8, 0))  # 08:00'ı belirliyoruz

    # Şu anki saati alıyoruz
    current_time = timezone.now()

    # Eğer kullanıcı 08:00'dan sonra giriş yapmışsa, geç kaldı
    if current_time > start_time:
        try:
            # Kullanıcının EmployeeDetails örneğini al
            employee = EmployeeDetails.objects.get(name=user.username)

            # Kullanıcının o gün ilk girişini al
            attendance = Attendance.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()

            if attendance and attendance.clock_in:
                lateness = (current_time - attendance.clock_in).total_seconds() / 60  # Gecikme süresi dakika cinsinden

                # Geç kalma kaydını oluştur
                lateness_record, created = LatenessRecord.objects.get_or_create(
                    employee=employee, 
                    date=timezone.now().date(),
                )
                lateness_record.lateness_minutes = lateness
                lateness_record.save()

                # Eğer bildirim daha önce gönderilmediyse, Celery ile bildirim gönder
                if not lateness_record.notification_sent:
                    send_late_notification.delay(user.id, lateness)  # Celery görevini çalıştır
                    lateness_record.notification_sent = True
                    lateness_record.save()
                                # Celery görevini çağırarak bildirim gönderiyoruz
                #send_late_notification.delay(user.username, lateness)  # Asenkron olarak çağırılıyor

        except Exception as e:
            print(f"Error checking lateness: {e}")
def dashboard(request):
    # Kullanıcı oturum açmışsa, Attendance modelinden verileri alın
    if request.user.is_authenticated:
        # 'EmployeeDetails' ve 'Attendance' modellerini kullanarak kullanıcının verilerini alın
        employee = EmployeeDetails.objects.get(name=request.user.username)
        notifications = Attendance.objects.filter(employee=employee)

        return render(request, 'dashboard.html', {'notifications': notifications})
    else:
        # Eğer kullanıcı giriş yapmamışsa, sadece 'notifications' boş dönülür
        return render(request, 'dashboard.html', {'notifications': []})

class Index(RedirectView):
    """
    Redirect view to the Home Page
    """
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return '/super-admin'
            else:
                return f'/employee/{self.request.user.id}'
        else:
            return '/login'
        
class AdminLogin(FormView):
    form_class = AuthenticationForm
    template_name = 'admin_login.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)

        if user is not None and user.is_superuser:
            if user.is_active:
                auth_login(self.request, user)

                return HttpResponseRedirect('/super-admin')
            else:
                messages.error(self.request, "User is not Active")
                return self.form_invalid(form)
        else:
            messages.error(self.request, "Invalid Credentials")
            return self.form_invalid(form)

class Login(FormView):
    form_class = AuthenticationForm
    template_name = 'login.html'

    def post(self, request):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None and not user.is_superuser:
            if user.is_active:
                auth_login(request, user)

                # Kullanıcı giriş yaptıktan sonra Attendance kaydını oluştur
                self.create_attendance_record(user)

                # Check if the user is late
                self.check_lateness(user)

                # Eğer kullanıcı için EmployeeDetails kaydı yoksa oluştur
                self.create_employee_details_if_not_exists(user)

                # Eğer superuser ise, super-admin sayfasına yönlendir
                if user.is_superuser:
                    return HttpResponseRedirect('/super-admin')
                else:
                    return HttpResponseRedirect(f'/user-dashboard')
            else:
                messages.error(self.request, "User is not Active")
                return HttpResponseRedirect('/')
        else:
            messages.error(self.request, "Invalid Credentials")
            return HttpResponseRedirect('/')

    def create_attendance_record(self, user):
        # Kullanıcı için Attendance kaydı oluşturuyoruz
        employee = EmployeeDetails.objects.get(name=user.username)

        attendance = Attendance(employee=employee, clock_in=timezone.now())
        attendance.save()
        print(f"Created attendance record for {user.username}")

    def check_lateness(self, user):
        start_time = timezone.make_aware(timezone.datetime.combine(timezone.now().date(), time(8, 0)))
        current_time = timezone.now()

        # Eğer şu anki zaman, 08:00'dan sonra ise, geç kalma kontrolü yapılacak
        if current_time > start_time:
            try:
                # Kullanıcının EmployeeDetails örneğini al
                employee = EmployeeDetails.objects.get(name=user.username)

                # Kullanıcının o günki ilk giriş kaydını al
                attendance = Attendance.objects.filter(employee=employee, clock_in__date=timezone.now().date()).first()

                if attendance and attendance.clock_in:
                    lateness_seconds = (attendance.clock_in - start_time).total_seconds()
                    lateness_minutes = lateness_seconds / 60

                    # Geç kalma kaydını oluştur
                    lateness_record, created = LatenessRecord.objects.get_or_create(
                        employee=employee, 
                        date=timezone.now().date(),
                    )
                    lateness_record.lateness_minutes = lateness_minutes
                    lateness_record.save()

                    # Yıllık izinden kesinti yapalım
                    if lateness_minutes > 0:
                        employee.no_of_remaining_leaves -= lateness_minutes / 60  # 1 saat için 1 saatlik kesinti yapar
                        employee.save()

                    # Bildirim göndermeyi unutma
                    if not lateness_record.notification_sent:
                        notification_message = f"{employee.name} is late by {lateness_minutes} minutes."
                        notification = Notification.objects.create(
                            user=user, 
                            message=notification_message,
                            is_read=False
                        )
                        notification.save()

                        lateness_record.notification_sent = True
                        lateness_record.save()

            except Exception as e:
                print(f"Error checking lateness: {e}")



    def create_employee_details_if_not_exists(self, user):
        # Kullanıcı için EmployeeDetails kaydını kontrol et
        if not EmployeeDetails.objects.filter(name=user.username).exists():
            # Eğer yoksa, yeni bir kayıt oluştur
            EmployeeDetails.objects.create(name=user.username, total_no_of_leaves=15)
            print(f"Created new EmployeeDetails record for {user.username}")



class LogoutView(RedirectView):
    url = '/login'

    def get(self, request, *args, **kwargs):
        # Kullanıcıyı çıkart
        user = request.user

        # Eğer kullanıcı superuser ise, çıkış kaydını tutma ve hemen logout işlemini yap
        if not user.is_superuser:
            # Kullanıcının EmployeeDetails nesnesini al
            try:
                employee = EmployeeDetails.objects.get(name=user.username)
            except EmployeeDetails.DoesNotExist:
                print(f"No EmployeeDetails found for {user.username}")
                employee = None

            # Kullanıcının son giriş kaydını al
            if employee:
                try:
                    attendance = Attendance.objects.filter(employee=employee).last()
                    if attendance and attendance.clock_out is None:  # Eğer çıkış yapılmamışsa
                        attendance.clock_out = timezone.now()  # Şu anki zamanı çıkış olarak kaydet
                        attendance.status = 'Absent'  # İstersen 'Absent' gibi bir status da ekleyebilirsin
                        attendance.save()  # Veriyi kaydet
                except Attendance.DoesNotExist:
                    print(f"No attendance record found for {employee.name}")

        # Kullanıcıyı çıkart
        auth_logout(request)

        # Logout işleminden sonra yönlendirme
        return super().get(request, *args, **kwargs)


class RegisterView(FormView):
    form_class = CustomUserCreationForm
    template_name = "register.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['rand'] = randint(100, 999)
        return ctx

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Kullanıcıyı oluştur
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']

            user = User.objects.create(username=username, email=email)
            user.set_password(password1)
            user.save()

            # Kullanıcıyı giriş yap
            auth_login(request, user)

            # EmployeeDetails kaydını oluştur
            employee = EmployeeDetails(name=username)
            employee.save()

            # Yeni Attendance kaydını oluştur
            attendance = Attendance(employee=employee, clock_in=timezone.now())  # İlk giriş anı
            attendance.save()

            # Yeni kullanıcı olduğu için is_new_user True yapıyoruz
            employee.is_new_user = True
            employee.save()

            return HttpResponseRedirect('/')
        else:
            messages.error(self.request, "Registration failed. Please try again!")
            return HttpResponseRedirect('/register')


class LogoutView(RedirectView):
    url = '/login'

    def get(self, request, *args, **kwargs):
        user = request.user

        # Eğer kullanıcı superuser ise, çıkış kaydını tutma ve hemen logout işlemini yap
        if not user.is_superuser:
            # Kullanıcının EmployeeDetails nesnesini al
            try:
                employee = EmployeeDetails.objects.get(name=user.username)
            except EmployeeDetails.DoesNotExist:
                print(f"No EmployeeDetails found for {user.username}")
                employee = None

            # Kullanıcının son giriş kaydını al
            if employee:
                try:
                    attendance = Attendance.objects.filter(employee=employee).last()
                    if attendance and attendance.clock_out is None:  # Eğer çıkış yapılmamışsa
                        attendance.clock_out = timezone.now()  # Şu anki zamanı çıkış olarak kaydet
                        attendance.status = 'Absent'  # İstersen 'Absent' gibi bir status da ekleyebilirsin
                        attendance.save()  # Veriyi kaydet
                except Attendance.DoesNotExist:
                    print(f"No attendance record found for {employee.name}")

        # Kullanıcıyı çıkart
        auth_logout(request)

        # Logout işleminden sonra yönlendirme
        return super().get(request, *args, **kwargs)


class Home(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs.get('pk'))
        employee = EmployeeDetails.objects.get(name=user.username)
        leaves = LeaveApplication.objects.filter(
            employee=employee.id).order_by('-date')

        # Check if the employee exceeds the leave limit
        if employee.no_of_remaining_leaves == 0:
            ctx['application_closed'] = True
            ctx['message'] = 'Your maximum leave is completed'
        else:
            ctx['application_closed'] = False

        if employee.no_of_applied_leaves >= 15:
            ctx['application_closed'] = True
            ctx['message'] = 'Your maximum leave application limit is reached'

        ctx['employee_name'] = employee.name
        ctx['no_of_leaves'] = employee.no_of_leaves
        ctx['no_of_remaining_leaves'] = employee.no_of_remaining_leaves
        ctx['total_leaves'] = employee.total_no_of_leaves
        ctx['leaves_list'] = []

        for leave in leaves:
            data = {}
            if leave.status == 'Waiting':
                data['show_delete_button'] = True
            elif leave.status == 'Approved':
                data['show_delete_button'] = False
            data['id'] = leave.id
            data['leave_type'] = leave.leave_type
            data['date'] = leave.date
            data['duration'] = leave.duration
            data['status'] = leave.status
            ctx['leaves_list'].append(data)

        ctx['rand'] = randint(100, 999)
        return ctx


class ApplyLeave(FormView):
    """ View to apply leave """
    def post(self, request):
        levae_type = self.request.POST.get('levae_type')
        duration = self.request.POST.get('DurationRadioOptions')
        date = self.request.POST.get('date')
        start_date = self.request.POST.get('start_date')
        end_date = self.request.POST.get('end_date')
        reason = self.request.POST.get('reason')

        employee = EmployeeDetails.objects.get(name=request.user)

        # Handle multiple days leave
        if start_date and end_date:
            # Parse the dates from 'YYYY-MM-DD' format
            date1 = datetime.strptime(start_date, '%Y-%m-%d')
            date2 = datetime.strptime(end_date, '%Y-%m-%d')

            # Calculate the difference in days
            delta = date2 - date1

            # Loop through the days in the date range
            for i in range(delta.days + 1):
                days = date1 + timedelta(days=i)

                # Create the leave application for each day
                leave = LeaveApplication()

                # Get the weekday name (e.g., 'Monday', 'Tuesday', etc.)
                week_day = calendar.day_name[days.weekday()]

                # Only apply leave for weekdays, not weekends
                if week_day != 'Saturday' and week_day != 'Sunday':
                    if int(employee.no_of_applied_leaves) <= 14:
                        employee.no_of_applied_leaves = float(employee.no_of_applied_leaves) + 1
                        employee.save()

                        leave.date = days
                        leave.leave_type = levae_type
                        leave.duration = 'Full Day'
                        leave.employee = employee
                        leave.description = reason
                        leave.save()

        # Handle single day or half-day leave
        elif date:
            leave = LeaveApplication()

            # Parse the single date from 'YYYY-MM-DD' format
            date = datetime.strptime(date, '%Y-%m-%d')

            # Get the weekday name for single day leave
            week_day = calendar.day_name[date.weekday()]

            # Only apply leave for weekdays, not weekends
            if week_day != 'Saturday' and week_day != 'Sunday':
                if int(employee.no_of_applied_leaves) <= 14:
                    if duration == 'Full Day':
                        employee.no_of_applied_leaves = float(employee.no_of_applied_leaves) + 1
                    elif duration == 'Half Day':
                        employee.no_of_applied_leaves = float(employee.no_of_applied_leaves) + 0.5
                    employee.save()

                    leave.date = date
                    leave.leave_type = levae_type
                    leave.duration = duration
                    leave.employee = employee
                    leave.description = reason
                    leave.save()

        # Redirect to the employee's page after applying the leave
        return HttpResponseRedirect(f'/user-dashboard/')


class DeleteLeaveApplication(LoginRequiredMixin, RedirectView):
    login_url = '/login/'

    def get_redirect_url(self, *args, **kwargs):
        user_id = self.request.user.id
        username = self.request.user.username

        url = f'/user-dashboard/'  # Redirect url

        id = kwargs['pk']  # Leave id
        employee = EmployeeDetails.objects.get(name=username)
        leave = LeaveApplication.objects.get(id=id)

        duration = leave.duration

        if duration == 'Half Day':
            employee.no_of_applied_leaves = float(employee.no_of_applied_leaves) - 0.5
        if duration == 'Full Day':
            employee.no_of_applied_leaves = float(employee.no_of_applied_leaves) - 1

        employee.save()
        leave.delete()  # Delete leave application

        return url

def record_entry_time(request):
    # Your logic for handling the entry time
    return HttpResponse("Entry time recorded!")


class SuperAdmin(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    redirect_field_name = '/super-admin/'
    template_name = 'superadmin.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # İzin başvurularını al
        leaves = LeaveApplication.objects.all().order_by('-date')

        # Kullanıcı login/logout zamanlarını al
        attendance_records = Attendance.objects.all().order_by('-clock_in')

        # Lateness records'ları al
        lateness_records = LatenessRecord.objects.all().order_by('-date')

        # Yeni kullanıcıları filtreleyin
        new_user_filter = self.request.GET.get('new_user', None)
        if new_user_filter == "True":
            employees = EmployeeDetails.objects.filter(is_new_user=True)
        elif new_user_filter == "False":
            employees = EmployeeDetails.objects.filter(is_new_user=False)
        else:
            employees = EmployeeDetails.objects.all()

        ctx['lateness_records'] = lateness_records
        ctx['employees'] = employees
        ctx['attendance_records'] = attendance_records
        ctx['leaves'] = leaves
        ctx['new_user_filter'] = new_user_filter

        return ctx


def lateness_records_view(request):
    lateness_records = LatenessRecord.objects.all()  # Tüm lateness records'larını al
    return render(request, 'lateness_records.html', {'lateness_records': lateness_records})

def login_logout_times_view(request):
    # Tüm attendance kayıtlarını al (giriş ve çıkış saatlerini içeriyor)
    attendance_records = Attendance.objects.all().order_by('-clock_in')  # Saatlere göre ters sıralama
    return render(request, 'login_logout_times.html', {'attendance_records': attendance_records})

from django.shortcuts import render
from .models import LeaveApplication

def leave_applications_view(request):
    # Tüm LeaveApplication kayıtlarını al (izin başvuruları)
    leave_applications = LeaveApplication.objects.all().order_by('-date')  # Tarihe göre ters sıralama
    return render(request, 'leave_applications.html', {'leave_applications': leave_applications})


class SaveLeaveStatus(LoginRequiredMixin, RedirectView):
    login_url = '/login/'
    url = '/super-admin'

    def get_redirect_url(self, *args, **kwargs):
        id = kwargs['pk']
        status = self.request.GET.get('status')
        employee_name = self.request.GET.get('employee')
        duration = self.request.GET.get('duration')

        leave = LeaveApplication.objects.get(id=id)
        employee = EmployeeDetails.objects.get(name=employee_name)

        leave.status = status
        leave.save()

        if status is not None:
            if status == 'Approved':
                if duration == 'Half Day':
                    employee.no_of_leaves = float(employee.no_of_leaves) + 0.5
                    employee.no_of_remaining_leaves = float(employee.no_of_remaining_leaves) - 0.5
                elif duration == 'Full Day':
                    employee.no_of_leaves = float(employee.no_of_leaves) + 1
                    employee.no_of_remaining_leaves = float(employee.no_of_remaining_leaves) - 1
            elif status == 'Not Approved':
                if duration == 'Half Day':
                    employee.no_of_leaves = float(employee.no_of_leaves) - 0.5
                    employee.no_of_remaining_leaves = float(employee.no_of_remaining_leaves) + 0.5
                elif duration == 'Full Day':
                    employee.no_of_leaves = float(employee.no_of_leaves) - 1
                    employee.no_of_remaining_leaves = float(employee.no_of_remaining_leaves) + 1
        employee.save()
        return super().get_redirect_url(*args, **kwargs)

@csrf_exempt
def send_late_notification(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        lateness_minutes = request.POST.get('lateness_minutes')
        send_late_notification.delay(user_id, lateness_minutes)
        return JsonResponse({'status': 'success', 'message': f'User {user_id} is late by {lateness_minutes} minutes.'})
    return JsonResponse({'status': 'failed'}, status=400)


from django.http import JsonResponse
from .models import Notification

def get_notifications(request):
    # Admin için tüm okunmamış bildirimleri getirme
    notifications = Notification.objects.filter(is_read=False)  # Tüm kullanıcılar için unread olanları alıyoruz
    notifications_data = [
        {
            "id": n.id,  # Bildirim ID'si
            "message": n.message,
            "created_at": n.created_at
        }
        for n in notifications
    ]
    
    # Return notifications as JSON
    return JsonResponse({"notifications": notifications_data})


def mark_notification_as_read(request, notification_id):
    try:
        # Bildirimi ID ile buluyoruz
        notification = Notification.objects.get(id=notification_id)
        
        # Bildirimi okundu olarak işaretliyoruz
        notification.is_read = True
        notification.save()
        
        return JsonResponse({"status": "success", "message": "Notification marked as read."})
    
    except Notification.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Notification not found."}, status=404)
    
def get_monthly_working_hours(request, user_id):
    # Belirtilen kullanıcıyı al
    user = User.objects.get(id=user_id)
    employee = EmployeeDetails.objects.get(name=user.username)
    
    # Bu ay içindeki tüm Attendance kayıtlarını al
    first_day_of_month = now().replace(day=1)
    last_day_of_month = now().replace(day=calendar.monthrange(now().year, now().month)[1])

    attendance_records = Attendance.objects.filter(
        employee=employee,
        clock_in__gte=first_day_of_month,
        clock_in__lte=last_day_of_month
    )

    total_hours = 0
    working_details = []

    # Her gün için çalışma saatlerini hesapla
    for record in attendance_records:
        if record.clock_out:
            worked_seconds = (record.clock_out - record.clock_in).total_seconds()
            worked_hours = worked_seconds / 3600  # Çalışma saatlerini saat cinsinden hesapla
            total_hours += worked_hours
            working_details.append({
                "date": record.clock_in.date(),
                "clock_in": record.clock_in,
                "clock_out": record.clock_out,
                "hours_worked": worked_hours
            })

    # PDF için istek yapıldıysa PDF oluştur ve gönder
    if 'download_pdf' in request.GET:
        template = get_template("monthly_working_hours_pdf.html")
        context = {
            "employee": employee.name,
            "total_working_hours": total_hours,
            "working_details": working_details,
            "month": now().strftime("%B %Y")
        }
        html = template.render(context)
        response = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type='application/pdf')
        return HttpResponse("Error generating PDF", status=500)

    # Ekranda gösterim için verileri döndür
    return render(request, "monthly_working_hours.html", {
        "employee": employee.name,
        "total_working_hours": total_hours,
        "working_details": working_details,
        "month": now().strftime("%B %Y"),
    })


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import LeaveApplication
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import EmployeeDetails, Attendance
from django.utils import timezone
import calendar
from reportlab.pdfgen import canvas

def monthly_working_hours_view(request):
    # Tüm personel için çalışma saatlerini hesaplayın
    first_day_of_month = timezone.now().replace(day=1)
    last_day_of_month = timezone.now().replace(day=calendar.monthrange(timezone.now().year, timezone.now().month)[1])

    employees = EmployeeDetails.objects.all()
    report_data = []

    for employee in employees:
        total_hours = 0
        attendance_records = Attendance.objects.filter(
            employee=employee,
            clock_in__gte=first_day_of_month,
            clock_in__lte=last_day_of_month
        )
        for record in attendance_records:
            if record.clock_out:
                worked_seconds = (record.clock_out - record.clock_in).total_seconds()
                total_hours += worked_seconds / 3600  # Saat cinsinden

        report_data.append({
            "employee": employee.name,
            "total_hours": round(total_hours, 2)
        })

    return render(request, 'monthly_working_hours.html', {"report_data": report_data})

def generate_monthly_report(request):
    first_day_of_month = timezone.now().replace(day=1)
    last_day_of_month = timezone.now().replace(day=calendar.monthrange(timezone.now().year, timezone.now().month)[1])

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monthly_working_hours.pdf"'

    pdf = canvas.Canvas(response)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 800, "Monthly Working Hours Report")
    y = 750

    employees = EmployeeDetails.objects.all()
    for employee in employees:
        total_hours = 0
        attendance_records = Attendance.objects.filter(
            employee=employee,
            clock_in__gte=first_day_of_month,
            clock_in__lte=last_day_of_month
        )
        for record in attendance_records:
            if record.clock_out:
                worked_seconds = (record.clock_out - record.clock_in).total_seconds()
                total_hours += worked_seconds / 3600  # Saat cinsinden

        pdf.drawString(100, y, f"Employee: {employee.name} - Total Hours: {round(total_hours, 2)}")
        y -= 20

    pdf.save()
    return response
@csrf_exempt
def save_leave_status(request):
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        status = request.POST.get('status')

        try:
            leave = LeaveApplication.objects.get(id=leave_id)
            leave.status = status
            leave.save()
            return JsonResponse({'success': True, 'message': 'Leave status updated successfully.'})
        except LeaveApplication.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Leave not found.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def user_login(request):
    msg = None
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            msg = "Invalid credentials. Please try again."

    return render(request, 'user_login.html', {"msg": msg})





@login_required
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:  # Sadece admin kullanıcılarına izin ver
        return redirect('login')
    return render(request, 'admin_dashboard.html')

from django.views import View
from django.shortcuts import render
from .models import LeaveApplication, EmployeeDetails

class UserDashboardView(View):
    def get(self, request):
        # Kullanıcı bilgilerini al
        user = request.user  # Şu an oturum açmış olan kullanıcı
        if not user.is_authenticated:
            return redirect('login')  # Kullanıcı giriş yapmadıysa login sayfasına yönlendir

        # EmployeeDetails modelinden kullanıcı bilgilerini al
        try:
            employee = EmployeeDetails.objects.get(name=user.username)
        except EmployeeDetails.DoesNotExist:
            return HttpResponse("Employee details not found.", status=404)

        # Kullanıcı izin bilgilerini al
        leaves = LeaveApplication.objects.filter(employee=employee).order_by('-date')

        # Toplam izin bilgileri
        total_leaves = employee.total_no_of_leaves
        leaves_taken = LeaveApplication.objects.filter(employee=employee, status="Approved").count()
        remaining_leaves = total_leaves - leaves_taken

        # Başvuru limitleri kontrolü
        application_closed = False
        message = ""
        if employee.no_of_remaining_leaves == 0:
            application_closed = True
            message = "Your maximum leave is completed"
        elif employee.no_of_applied_leaves >= 15:
            application_closed = True
            message = "Your maximum leave application limit is reached"

        # İzin listesi
        leaves_list = []
        for leave in leaves:
            data = {
                "id": leave.id,
                "leave_type": leave.leave_type,
                "date": leave.date,
                "duration": leave.duration,
                "status": leave.status,
                "show_delete_button": leave.status == "Waiting"
            }
            leaves_list.append(data)

        # Context verilerini hazırla
        context = {
            "employee_name": employee.name,
            "total_leaves": total_leaves,
            "no_of_leaves": leaves_taken,
            "no_of_remaining_leaves": remaining_leaves,
            "leaves_list": leaves_list,
            "application_closed": application_closed,
            "message": message,
            "rand": randint(100, 999),
        }

        # Template'e verileri gönder
        return render(request, "user_dashboard.html", context)

    
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LeaveApplication, EmployeeDetails
from datetime import datetime

class ApplyLeaveView(View):
    def get(self, request):
        # Kullanıcı bilgilerini al
        user = request.user  # Şu an oturum açmış olan kullanıcı
        if not user.is_authenticated:
            return redirect('login')  # Kullanıcı giriş yapmadıysa login sayfasına yönlendir

        # EmployeeDetails modelinden kullanıcı bilgilerini al
        try:
            employee = EmployeeDetails.objects.get(name=user.username)
        except EmployeeDetails.DoesNotExist:
            return HttpResponse("Employee details not found.", status=404)

        # Kullanıcı izin bilgilerini al
        leaves = LeaveApplication.objects.filter(employee=employee).order_by('-date')

        # Toplam izin bilgileri
        total_leaves = employee.total_no_of_leaves
        leaves_taken = LeaveApplication.objects.filter(employee=employee, status="Approved").count()
        remaining_leaves = total_leaves - leaves_taken

        # Başvuru limitleri kontrolü
        application_closed = False
        message = ""
        if employee.no_of_remaining_leaves == 0:
            application_closed = True
            message = "Your maximum leave is completed"
        elif employee.no_of_applied_leaves >= 15:
            application_closed = True
            message = "Your maximum leave application limit is reached"

        # İzin listesi
        leaves_list = []
        for leave in leaves:
            data = {
                "id": leave.id,
                "leave_type": leave.leave_type,
                "date": leave.date,
                "duration": leave.duration,
                "status": leave.status,
                "show_delete_button": leave.status == "Waiting"
            }
            leaves_list.append(data)

        # Context verilerini hazırla
        context = {
            "employee_name": employee.name,
            "total_leaves": total_leaves,
            "no_of_leaves": leaves_taken,
            "no_of_remaining_leaves": remaining_leaves,
            "leaves_list": leaves_list,
            "application_closed": application_closed,
            "message": message,
            "rand": randint(100, 999),
        }

        # Template'e verileri gönder
        return render(request, "apply_leave.html", context)

from django.views import View
from django.shortcuts import render
from .models import LeaveApplication

class LeaveListView(View):
    def get(self, request):
        # Kullanıcı bilgilerini al
        user = request.user  # Şu an oturum açmış olan kullanıcı
        if not user.is_authenticated:
            return redirect('login')  # Kullanıcı giriş yapmadıysa login sayfasına yönlendir

        # EmployeeDetails modelinden kullanıcı bilgilerini al
        try:
            employee = EmployeeDetails.objects.get(name=user.username)
        except EmployeeDetails.DoesNotExist:
            return HttpResponse("Employee details not found.", status=404)

        # Kullanıcı izin bilgilerini al
        leaves = LeaveApplication.objects.filter(employee=employee).order_by('-date')

        # Toplam izin bilgileri
        total_leaves = employee.total_no_of_leaves
        leaves_taken = LeaveApplication.objects.filter(employee=employee, status="Approved").count()
        remaining_leaves = total_leaves - leaves_taken

        # Başvuru limitleri kontrolü
        application_closed = False
        message = ""
        if employee.no_of_remaining_leaves == 0:
            application_closed = True
            message = "Your maximum leave is completed"
        elif employee.no_of_applied_leaves >= 15:
            application_closed = True
            message = "Your maximum leave application limit is reached"

        # İzin listesi
        leaves_list = []
        for leave in leaves:
            data = {
                "id": leave.id,
                "leave_type": leave.leave_type,
                "date": leave.date,
                "duration": leave.duration,
                "status": leave.status,
                "show_delete_button": leave.status == "Waiting"
            }
            leaves_list.append(data)

        # Context verilerini hazırla
        context = {
            "employee_name": employee.name,
            "total_leaves": total_leaves,
            "no_of_leaves": leaves_taken,
            "no_of_remaining_leaves": remaining_leaves,
            "leaves_list": leaves_list,
            "application_closed": application_closed,
            "message": message,
            "rand": randint(100, 999),
        }

        # Template'e verileri gönder
        return render(request, "leave_list.html", context)


from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import EmployeeDetails

# Süper kullanıcı kontrolü
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def update_employee_leaves(request):
    employees = EmployeeDetails.objects.all()

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        extra_leaves = request.POST.get("extra_leaves")

        # Çalışanı al
        try:
            employee = EmployeeDetails.objects.get(id=employee_id)
        except EmployeeDetails.DoesNotExist:
            return HttpResponse("Employee not found.", status=404)

        # Ekstra izin günlerini ekle
        try:
            extra_leaves = float(extra_leaves)
            employee.no_of_remaining_leaves += extra_leaves
            employee.total_no_of_leaves += extra_leaves
            employee.save()
        except ValueError:
            return HttpResponse("Invalid leave value.", status=400)

        return redirect("update_employee_leaves")  # İşlem sonrası aynı sayfaya dön

    context = {
        "employees": employees,
    }
    return render(request, "update_employee_leaves.html", context)
