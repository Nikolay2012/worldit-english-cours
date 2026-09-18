from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
import json
from .models import *

# Create your views here.

@require_http_methods(["GET", "POST"])
def render_login(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username = username, password = password)
        if user is not None:
            login(request, user)
            return JsonResponse({'error': False})

        return JsonResponse({'error': 'Invalid login data'}, status = 401)

    return render(request, "users/login.html")

@require_GET
def logout_user(request: HttpRequest):
    logout(request)
    return redirect("login")


@require_GET
@login_required
# Порожня головна сторінка для тестування
def rendet_debug_main(request: HttpRequest):
    return render(request, "users/debug_main.html")