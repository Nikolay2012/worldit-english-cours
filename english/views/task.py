"""
Страница задания курса английского

Маршрут:
GET /courses/english/modules/<module_id>/lessons/<lesson_id>/tasks/<task_id>/
(name="english:english_task", адрес собирает EnglishTask.get_absolute_url)

Доступ - admin, mentor, student

Задание ищется только внутри указанного урока, модуля и курса английского
Если задание не найдено (например, его удалили):
-модуль существует - переадресация на страницу модуля
-модуля тоже нет - 404

Кто что видит:
-персонал (admin, mentor) видит любое задание
-студент видит задание, только если оно ему открыто (EnglishTaskService.can_access)
иначе - переадресация на страницу модуля с сообщением «Це завдання ще не відкрите.»

Что показывается на странице (content_component):
-персонал, у задания есть шаги - staff_preview
-персонал, шагов нет - import_csv
-студент, у задания есть шаги - student_run
-студент, шагов нет - empty

Что передаётся в шаблон english/task.html:
-task - задание
-content_component - путь к шаблону компонента
-can_import - показывать ли кнопку «Завантажити» (персонал и шагов нет)
-header_links - хлебные крошки
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from WorldIT.decorators import required_type
from WorldIT.settings import ENGLISH_COURSE_ID
from courses.models import Lesson, Module
from english.models import EnglishTask
from english.services.task import EnglishTaskService


ACCESS_TYPES = ["admin", "mentor", "student"]
STAFF_TYPES = ["admin", "mentor"]

@method_decorator(
    required_type(ACCESS_TYPES),
    # предположительно, что в дальнейшем будут и другие методы запроса помимо get
    # если не будет - уберу name="dispatch"
    name="dispatch"
)
class EnglishTaskView(DetailView):
    
    http_method_names = ["get"]
    template_name = "english/task.html"
    context_object_name = "task"
    
    def get_queryset(self):
        return EnglishTask.objects.filter(
            lesson__module__course_id=ENGLISH_COURSE_ID,
            lesson__module_id=self.kwargs["module_id"],
            lesson_id=self.kwargs["lesson_id"]
        ).select_related("lesson__module")
    
    def get(self, request, *args, **kwargs):
        
        try:
            self.object = self.get_object()
        except Http404:
            return self._redirect_to_module_or_404()
        
        if not self._is_staff() and not self._student_can_acess():
            messages.info(request, "Це завдання ще не відкрите.")
            return redirect(self._get_module_url())
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def _redirect_to_module_or_404(self):
        """
        В случае, если задание не было найдено, 
        а пользователь попытался попасть на страницу этого задания
        
        Его либо переадресует на страницу модуля (если модуль существует)
        Либо выбросит 404
        """
        
        module_id = self.kwargs["module_id"]
        
        module_exists = Module.objects.filter(
            pk=module_id,
            course_id=ENGLISH_COURSE_ID,
        ).exists()
        
        if not module_exists:
            raise Http404
        
        return redirect(
            reverse("english:english_module", args=[module_id])
        )
    
    def _student_can_acess(self) -> bool:
        
        student = self._get_student()
        
        return student is not None and EnglishTaskService(self.object).can_access(student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        has_steps = EnglishTaskService(self.object).has_steps()
        
        context.update(
            can_import=self._is_staff() and not has_steps,
            content_component=self._get_content_component(has_steps=has_steps),
            header_links=self._get_header_links(),
            can_open_words_list=has_steps and self.object.type == "words",
        )
        
        return context
    
    def _get_module_url(self) -> str:
        return reverse("english:english_module", args=[self.object.lesson.module_id])
    
    def _get_header_links(self) -> list[tuple]:
        
        lesson: Lesson = self.object.lesson
        module: Module = lesson.module
        
        return [
            ("Курси", "all_courses"),
            ("English", "english:all_english_modules"),
            (
                f"Модуль №{module.pk}", 
                reverse("english:english_module", args=[module.pk])
            ), # вместо module_pk должен быть order_number. Но его, на данный момент, нету в модели Module
            (
                f"Урок №{lesson.pk}",
                self.object.get_absolute_url()
            )
        ]
    
    def _get_content_component(self, has_steps: bool) -> str:
        
        if self._is_staff():
            component = "run" if has_steps else "import_csv"
        else:
            component = "run" if has_steps else "empty"
            
        return f"english/components/task/{component}.html"
    
    def _is_staff(self) -> bool:
        
        account_types = self.request.user.account_types
        
        for staff_type in STAFF_TYPES:
            if staff_type in account_types:
                return True
        
        return False
    
    def _get_student(self):
        return getattr(self.request.user, "profile_student", None)
