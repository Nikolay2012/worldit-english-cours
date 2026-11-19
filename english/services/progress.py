"""

"""

from django.conf import settings
from django.db.models import F
from django.db.models.aggregates import Count
from english.models.english_task import EnglishTask
from english.models.student_progress import StudentProgress
from users.models import Student


# Подсчет процента прогресса идёт исключительно для студента,
# ведь только у студента происходит запись прогресса в базу
class EnglishProgressService:
    def __init__(self, student: Student):
        self.student = student
        self.REQUIRED_CORRECT_ANSWERS = 6
        
        self.tasks = None
        self.correct_by_task = None
    
    def get_task_percent(
            self, 
            steps_count: int, 
            correct_count: int
        ) -> int:
        
        if steps_count == 0:
            return 0
        
        # min для старіх шагов, на которіе студенті уже ответили 
        # до віпуска фикса багов в работе заданий "Слова"
        return min(
            100, 
            round(
                correct_count / (steps_count * self.REQUIRED_CORRECT_ANSWERS) * 100
            )
        )
    
    # Возвращает пару: id задания - колво прав. ответов
    def _get_correct_by_task(self) -> dict[int, int]:
        if self.correct_by_task is None:
            self.correct_by_task = dict(
                StudentProgress.objects.filter(
                    student=self.student,
                    task__lesson__module__course_id=settings.ENGLISH_COURSE_ID
                ).values_list("task_id", "correct_count")
            )
        
        return self.correct_by_task
    
    def _get_tasks(self) -> list[EnglishTask]:
        
        if self.tasks is None:
            self.tasks = list(
                EnglishTask.objects.filter(
                    lesson__module__course_id=settings.ENGLISH_COURSE_ID,
                    # ОЧевидно, прогресс подсчитывает только по активным заданиям,
                    # т. е. тем, что не находятся в архиве
                    is_active=True
                ).annotate(
                    steps_count=Count("steps"),
                    lesson_module_id=F("lesson__module_id")
                ).filter(
                    # По сути, фильтр только на те задания, 
                    # которые проходились (частично или полнлстью)
                    # Ведь если в задании не было дано ещё ни одного правильного ответа - то и шагов нету
                    steps_count__gt=0
                )
            )
        
        return self.tasks
    
    # Необходимо скорее для подсчета прогресса по модулю
    # но може понадобится еще где-то
    # пока не отмечаю, что метод приватный
    def get_tasks_percents(self) -> dict[int, int]:
        
        correct_by_task = self._get_correct_by_task()
        
        return {
            task.id: self.get_task_percent(
                correct_count=correct_by_task.get(task.id, 0),
                steps_count=task.steps_count
            ) for task in self._get_tasks()
        }
    
    def get_modules_percents(self) -> dict[int, int]:
        
        task_percents = self.get_tasks_percents()
        # процент прохождения каждого модуля студентом
        percents_by_module = {}
        
        for task in self._get_tasks():
            percents_by_module.setdefault(task.lesson_module_id, []).append(
                task_percents[task.id]
            )
        
        return {
            module_id: sum(percents) // len(percents) for module_id, percents in percents_by_module.items()
        }
    
    def get_course_percent(self) -> int:
        
        module_percents = list(
            self.get_modules_percents().values()
        )
        
        if not module_percents:
            return 0
        
        return sum(module_percents) // len(module_percents)
