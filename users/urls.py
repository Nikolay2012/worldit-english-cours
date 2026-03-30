from .views import *
from django.urls import path

urlpatterns = [
    path('login', render_login, name='login'),
    path('logout', logout_user, name="logout"),
    path('mentors', render_mentors, name='mentors'),
    path('students', render_students, name='students')
]