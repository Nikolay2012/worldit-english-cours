from .views import *
from django.urls import path

urlpatterns = [
    path('all/', rendet_all_courses, name = "all_courses"),
    path('completed/', rendet_completed_courses, name = "completed_courses"),
    path('my/', rendet_my_courses, name = "my_courses"),
]