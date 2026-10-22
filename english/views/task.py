from django.http import Http404
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
    
    def get_object(self, queryset=None):
        
        self.object: EnglishTask = super().get_object(queryset)
        
        if self._is_staff():
            return self.object
        
        student = self._get_student()
        
        if student is None or \
            not EnglishTaskService(self.object).can_access(student):
            raise Http404
        
        return self.object
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        has_steps = EnglishTaskService(self.object).has_steps()
        
        context.update(
            content_component=self._get_content_component(has_steps=has_steps),
            header_links=self._get_header_links(),
        )
        
        return context
    
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

        return f"components/{component}.html"
    
    def _is_staff(self) -> bool:
        
        account_types = self.request.user.account_types
        
        for staff_type in STAFF_TYPES:
            if staff_type in account_types:
                return True
        
        return False
    
    def _get_student(self):
        return getattr(self.request.user, "student", None)
