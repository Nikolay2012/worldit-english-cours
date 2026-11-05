"""
Страница одного модуля курса английского: уроки и их задания

Маршрут:
GET /courses/english/modules/<pk>/ (name="english:english_module")

Доступ - student, manager, admin
(нужен ли доступ для manager - уточнить у команды)

Что показывает страница:
-уроки модуля по порядку (order_number)
-у каждого урока задания разделены на два блока по полю block:
    -lesson.main_lesson_tasks - основной урок (block="lesson")
    -lesson.homework_tasks - домашняя практика (block="homework")
-задания внутри блока идут по order

Модуль ищется только среди модулей курса английского (settings.ENGLISH_COURSE_ID),
поэтому модуль из другого курса по этому адресу даст 404

Для студента у каждого задания отображается:
-заблокировано ли оно (не открыто студенту или недоступно) - по opened_task_ids
-процент прохождения и выполнено ли оно - по его записи StudentProgress
Персонал видит все задания открытыми и без прогресса

Прогресс прикрепляется к заданиям временными атрибутами (не поля модели,
в БД не сохраняются) - метод ._attach_tasks_progress():
-task.progress_percent - процент прохождения: правильные ответы / (шагов × 6)
-task.is_completed - задание выполнено (status = "completed")

Запросов к БД не зависит от количества уроков:
модуль, уроки, по одному prefetch на каждый блок заданий,
прогресс студента, количество шагов заданий, открытые студенту задания

Что передаётся в шаблон english/module.html:
-lessons_and_tasks - уроки модуля с заданиями по блокам (с прогрессом у заданий)
-module - текущий модуль
-is_staff - персонал (видит все задания открытыми, без процента)
-opened_task_ids - id заданий, открытых студенту
-header_links - хлебные крошки
-can_edit - может ли редактировать уроки (admin)
-can_add - может ли добавлять задания (admin)

Пагинации уроков пока нет
Чтобы включить, достаточно добавить paginate_by,
тогда задания будут загружаться только для уроков текущей страницы
"""

from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.aggregates import Count
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.conf import settings

from WorldIT.decorators import required_type
from courses.models import Lesson, Module
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.models.open_english_task import OpenEnglishTask
from english.models.student_progress import StudentProgress


@method_decorator(
    # Нужен ли доступ для "manager"?
    required_type(["student", "manager", "admin"]),
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
                queryset=self._get_tasks_queryset(block="lesson"),
                to_attr="main_lesson_tasks"
            ),
            Prefetch(
                lookup="english_tasks",
                queryset=self._get_tasks_queryset(block="homework"),
                to_attr="homework_tasks"
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        self._attach_tasks_progress(lessons=context["object_list"])
        
        context.update(
            module=self.module,
            is_staff=self._is_staff(),
            header_links=self._get_header_links(),
            opened_task_ids=self._get_opened_task_ids(),
            **self._get_permissions()
        )
        
        return context
    
    def _attach_tasks_progress(self, lessons):
        
        student = getattr(self.request.user, "profile_student", None)
        
        progress_by_task = {}
        
        if student is not None and not self._is_staff():
            progress_by_task = {
                progress.task_id: progress for progress in StudentProgress.objects.filter(
                    student=student,
                    task__lesson__module=self.module
                )
            }
        
        steps_count_by_task = dict(
            EnglishTask.objects.filter(
                lesson__module=self.module
            ).annotate(
                steps_count=Count("steps")
            ).values_list("id", "steps_count")
        )
        
        for lesson in lessons:
            for task in lesson.main_lesson_tasks + lesson.homework_tasks:
                progress = progress_by_task.get(task.id)
                steps_count = steps_count_by_task.get(task.id, 0)
                
                # Временные атрибуты
                # Всеравно будем передавать задание на шаблон
                task.progress_percent = 0
                task.is_completed = False
                
                if progress is not None and steps_count:
                    task.progress_percent = round(
                        progress.correct_count / (steps_count * 6) * 100
                    )
                    task.is_completed = True if progress.status == "completed" else False
    
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
        
        return {
            "can_edit": is_admin,
            "can_add": is_admin
        }
    
    def _is_staff(self) -> bool:
        
        account_types = self.request.user.account_types
        
        for staff_type in ["admin"]:
            if staff_type in account_types:
                return True
        
        return False
    
    def _get_student(self):
        return getattr(self.request.user, "profile_student", None)
    
    def _get_opened_task_ids(self) -> set[int]:
        
        student = self._get_student()
        
        if student is None:
            return set()
        
        return set(
            OpenEnglishTask.objects.filter(
                student=student,
                task__lesson__module=self.module,
                task__is_available=True
            # flat=True, чтобы возвращались чисто значения, а не кортежи
            ).values_list("task_id", flat=True)
        )
    
    def _get_tasks_queryset(self, block: str):
        
        tasks = EnglishTask.objects.filter(
            block=block
        ).order_by("order")
        
        if self._is_staff():
            return tasks
        
        return tasks.filter(
            Exists(
                EnglishTaskStep.objects.filter(task=OuterRef("pk"))
            )
        )
