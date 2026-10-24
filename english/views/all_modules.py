"""
Сторінка списку модулів курсу English.

Маршрут:
    GET /courses/english/modules/            (name="english:all_english_modules")
    GET /courses/english/modules/?page=2     пагінація

Доступ:
    student, mentor, manager, admin
    (доступ для manager — уточнити в команди).

Що показує:
    модулі курсу English (settings.ENGLISH_COURSE_ID) по 10 на сторінці,
    у порядку id — поки в моделі Module немає order_number.

Контекст шаблону english/all_modules.html:
    modules       — модулі поточної сторінки
    page_obj      — поточна сторінка (номер, сусідні сторінки)
    paginator     — уся вибірка (кількість сторінок)
    is_paginated  — чи більше однієї сторінки
    course        — курс English (назва в заголовку)
    header_links  — хлібні крихти
"""

from django.shortcuts import get_object_or_404
from WorldIT.decorators import required_type
from django.utils.decorators import method_decorator
from WorldIT.settings import ENGLISH_COURSE_ID
from courses.models import Course, Module
from django.views.generic import ListView


# Нужен ли доступ для "manager"?
@method_decorator(
    required_type(["student", "mentor", "manager", "admin"]),
    name="get"
)
class AllModulesView(ListView):
    
    model = Module
    template_name = "english/all_modules.html"
    context_object_name = "modules"
    http_method_names = ["get"]
    paginate_by = 10
    
    def get_queryset(self):
        modules = Module.objects.filter(
            course_id=ENGLISH_COURSE_ID
        ).order_by("id")
        
        return modules
    
    def get_context_data(self, **kwargs):
        
        english_course = get_object_or_404(Course, pk=ENGLISH_COURSE_ID)
        
        
        context = super().get_context_data(**kwargs)
        
        context["course"] = english_course
        context["header_links"] = [
            ("Курси", "all_courses"),
            ("English", "english:all_english_modules")
        ]
        
        return context
