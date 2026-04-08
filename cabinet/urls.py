from .views import *
from django.urls import path

urlpatterns = [
    path('', render_dashboard, name = "dashboard"),
    path('settings/', render_settings, name="settings"),
    path('schedule/', render_schedule, name="schedule"),
    path('payment/', render_payment, name="payment"),
    path("notification/", render_notification, name="notification"),
    path("administration/", render_administration, name="administration"),
]