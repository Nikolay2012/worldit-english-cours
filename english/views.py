from django.http import HttpRequest
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from WorldIT import settings
from WorldIT.decorators import required_type
from WorldIT.settings import ENGLISH_COURSE_ID
from courses.models import Course, Lesson, Module
from english.models.english_task import EnglishTask

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
def render_module(request: HttpRequest, pk: int):
    
    module = get_object_or_404(
        Module, 
        pk=pk,
        # чтобы получать только модули курса английского
        # а не модули из курса python, java и прочих
        course_id=settings.ENGLISH_COURSE_ID
    )
    
    lessons = Lesson.objects.filter(
        module_id=module.id
    )
    
    lessons_and_tasks = []
    
    for lesson in lessons:
        lesson: Lesson
        
        tasks = EnglishTask.objects.filter(
            lesson_id=lesson.id
        )
        
        main_lesson_tasks = []
        homework_tasks = []
        
        for task in tasks:
            task: EnglishTask
            
            if task.block == "lesson":
                main_lesson_tasks.append(task)
            elif task.block == "homework":
                homework_tasks.append(task)
        
        lessons_and_tasks.append({
            "lesson": lesson,
            "main_lesson_tasks": main_lesson_tasks,
            "homework_tasks": homework_tasks
        })
    
    return render(
        request=request, 
        template_name="english/module.html",
        context={
            "module": module,
            "lessons_and_tasks": lessons_and_tasks,
            "header_links": [
                ("Курси", "all_courses"),
                ("English", "english:all_english_modules"),
                (f"Модуль №{module.pk}", reverse("english:english_module", args=[module.pk])) # вместо module_pk должен быть order_number. Но его, на данный момент, нету в модели Module
            ]
        }
    )
