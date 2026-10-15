from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from WorldIT.decorators import required_type
from WorldIT.settings import ENGLISH_COURSE_ID
from courses.models import Course, Module

# Create your views here.
@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def render_all_modules(request: HttpRequest):
    
    english_course = get_object_or_404(Course, pk=ENGLISH_COURSE_ID)
    # Отдельно, если нужно будет фильтровать модули из архива
    modules = Module.objects.filter(
        course=english_course
    )
    
    return render(
        request=request, 
        template_name="english/all_modules.html",
        context={
            "course": english_course,
            "modules": modules,
            "header_links": [
                ("Курси", "all_courses"),
                ("English", "english:all_english_modules")
            ]
        }
    )

@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def render_module(request: HttpRequest, module_id: int):
    
    return render(
        request=request, 
        template_name="english/module.html"
    )
