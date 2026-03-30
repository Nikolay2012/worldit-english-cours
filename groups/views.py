from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from .models import *


@require_GET
@required_type("admin")
def rendet_all_groups(request: HttpRequest):
    return render(request, "groups/all_groups.html")

@require_GET
@login_required
def rendet_my_groups(request: HttpRequest):
    return render(request, "groups/my_groups.html")

@require_GET
@required_type(["admin", "mentor", "manager"])
def rendet_archive_groups(request: HttpRequest):
    return render(request, "groups/archive_groups.html")