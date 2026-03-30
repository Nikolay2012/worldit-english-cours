from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from .models import *

@require_http_methods(["GET"])
def render_menu(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return redirect("login")