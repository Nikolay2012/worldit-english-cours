from .views import *
from django.urls import path

urlpatterns = [
    path('login', render_login, name='login'),
    path('logout', logout_user, name="logout"),
    path('mentors', render_mentors, name='mentors'),
    path('archive_mentors', render_archive_mentors, name = "archive_mentors"),
    path("my_students", render_my_students, name="my_students"),
    path('all_students', render_all_students, name='all_students'),
    path('archive_students', render_archive_students, name='archive_students')
]