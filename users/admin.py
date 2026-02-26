from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register([CustomUser, Mentor, Manager, Parent, Student])