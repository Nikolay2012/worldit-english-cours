from .views import *
from django.urls import path

urlpatterns = [
    path('all/', rendet_all_groups, name = "all_groups"),
    path('my/', rendet_my_groups, name = "my_groups"),
    path('archive/', rendet_archive_groups, name = "archive_groups"),
]