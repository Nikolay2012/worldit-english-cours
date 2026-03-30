from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from .models import *


@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def rendet_all_courses(request: HttpRequest):
    return render(request, "courses/all_courses.html")

@require_GET
@required_type("student")
def rendet_completed_courses(request: HttpRequest):
    return render(request, "courses/completed_courses.html")

@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def rendet_my_courses(request: HttpRequest):
    return render(request, "courses/my_courses.html")