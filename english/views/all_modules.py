"""
Страница списка модулей курса английского

Маршрут:
GET /courses/english/modules/ (name="english:all_english_modules")
GET /courses/english/modules/?page=2 - пагинация

Доступ - student, manager, admin
(нужен ли доступ для manager - уточнить у команды)

Что показывает страница:
-модули курса английского (settings.ENGLISH_COURSE_ID), по 10 на странице
-модули идут по id, пока в модели Module нет order_number

Если курса английского нет в БД, или номер страницы больше,
чем страниц всего, будет 404

Что передаётся в шаблон english/all_modules.html:
-modules - модули текущей страницы
-page_obj - текущая страница (номер, соседние страницы)
-paginator - вся выборка (сколько всего страниц)
-is_paginated - больше ли одной страницы
-course - курс английского (название в заголовке)
-header_links - хлебные крошки
-is_staff - персонал (admin)
"""

from django.shortcuts import get_object_or_404
from WorldIT.decorators import required_type
from django.utils.decorators import method_decorator
from django.conf import settings

from courses.models import Course, Module
from django.views.generic import ListView


# Нужен ли доступ для "manager"?
@method_decorator(
    required_type(["student", "manager", "admin"]),
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
            course_id=settings.ENGLISH_COURSE_ID
        ).order_by("id")
        
        return modules
    
    def get_context_data(self, **kwargs):
        
        english_course = get_object_or_404(Course, pk=settings.ENGLISH_COURSE_ID)
        
        
        context = super().get_context_data(**kwargs)
        
        context["course"] = english_course
        context["header_links"] = [
            ("Курси", "all_courses"),
            ("English", "english:all_english_modules")
        ]
        context["is_staff"] = self._is_staff()
        
        return context
    
    def _is_staff(self) -> bool:
            
            account_types = self.request.user.account_types
            
            for staff_type in ["admin", "mentor"]:
                if staff_type in account_types:
                    return True
            
            return False
