from django.db.models import Prefetch
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from WorldIT import settings
from WorldIT.decorators import required_type
from courses.models import Lesson, Module
from english.models.english_task import EnglishTask


@method_decorator(
    # Нужен ли доступ для "manager"?
    required_type(["student", "mentor", "manager", "admin"]),
    name="get"
)
class ModuleView(ListView):
    
    http_method_names = ["get"]
    context_object_name = "lessons_and_tasks"
    template_name = "english/module.html"
    
    def get_queryset(self):
        
        self.module = get_object_or_404(
            Module, 
            pk=self.kwargs["pk"],
            # чтобы получать только модули курса английского
            # а не модули из курса python, java и прочих
            course_id=settings.ENGLISH_COURSE_ID
        )
        
        return Lesson.objects.filter(
            module=self.module
        # С prefetch_related для удобства,
        # чтобы в одном месте получить и уроки и задания
        # Задания разделены по типам уточнением Prefetch()
        # В шаблоне module.html можно увидеть, 
        # что задания отображаются по двум блокам: main_lesson_tasks и homework_tasks
        # Именно здесь и происходит разделение заданий по блокам
        ).order_by("order_number").prefetch_related(
            Prefetch(
                lookup="english_tasks",
                queryset=EnglishTask.objects.filter(block="lesson").order_by("order"),
                to_attr="main_lesson_tasks"
            ),
            Prefetch(
                lookup="english_tasks",
                queryset=EnglishTask.objects.filter(block="homework").order_by("order"),
                to_attr="homework_tasks"
            )
        )
        
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update(
            module=self.module,
            header_links=self._get_header_links(),
            **self._get_permissions()
        )
        
        return context
    
    def _get_header_links(self) -> list[tuple]:
        return [
            ("Курси", "all_courses"),
            ("English", "english:all_english_modules"),
            (
                f"Модуль №{self.module.pk}", 
                reverse("english:english_module", args=[self.module.pk])
            ) # вместо module_pk должен быть order_number. Но его, на данный момент, нету в модели Module
        ]
    
    def _get_permissions(self) -> dict[str, bool]:
        
        account_types = self.request.user.account_types
        is_admin = "admin" in account_types
        is_mentor = "mentor" in account_types
        
        return {
            "can_edit": is_admin,
            "can_add": is_admin or is_mentor
        }
