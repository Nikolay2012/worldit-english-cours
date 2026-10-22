from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
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
        
        self.object = self.get_object()
        
        if not self._is_staff() and not self._student_can_acess():
            messages.info(request, "Це завдання ще не відкрите.")
            return redirect(self._get_module_url())
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def _student_can_acess(self) -> bool:
        
        student = self._get_student()
        
        return student is not None and EnglishTaskService(self.object).can_access(student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        has_steps = EnglishTaskService(self.object).has_steps()
        
        context.update(
            can_import=True,
            content_component=self._get_content_component(has_steps=has_steps),
            header_links=self._get_header_links(),
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
            component = "staff_preview" if has_steps else "import_csv"
        else:
            component = "student_run" if has_steps else "empty"

        return f"english/components/{component}.html"
    
    def _is_staff(self) -> bool:
        
        account_types = self.request.user.account_types
        
        for staff_type in STAFF_TYPES:
            if staff_type in account_types:
                return True
        
        return False
    
    def _get_student(self):
        return getattr(self.request.user, "profile_student", None)
