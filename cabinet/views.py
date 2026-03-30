from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from .models import *

@require_GET
@login_required
def render_dashboard(request: HttpRequest):
    return render(request, "cabinet/dashboard.html")

@require_GET
@login_required
def render_settings(request: HttpRequest):
    return render(request, "cabinet/settings.html")

@require_GET
@required_type("parent")
def render_payment(request: HttpRequest):
    return render(request, "cabinet/payment.html")

@require_GET
@login_required
def render_schedule(request: HttpRequest):
    return render(request, "cabinet/schedule.html")

@require_GET
@login_required
def render_notification(request: HttpRequest):
    return render(request, "cabinet/notification.html")

@require_GET
@required_type("parent")
def render_my_students(request: HttpRequest):
    return render(request, "cabinet/my_students.html")