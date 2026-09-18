from .views import *
from django.urls import path

urlpatterns = [
    path('login', render_login, name='login'),
    path('logout', logout_user, name="logout"),
    path("", rendet_debug_main, name="debug_main")
]