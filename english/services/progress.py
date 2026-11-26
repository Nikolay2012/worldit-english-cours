"""
Сервис подсчёта прогресса студента по курсу английского

Используется:
-TaskRunner - процент одного задания (.get_task_percent())
-AllModulesView - проценты модулей (.get_modules_percents())
-страница курсов (courses) - процент курса (.get_course_percent()),
подключение описано в README.md

Прогресс считается только для студента:
записи прогресса (StudentProgress) есть только у него
Для персонала сервис не создаётся

Использование:
EnglishProgressService(student).get_task_percent(steps_count, correct_count) - процент задания
EnglishProgressService(student).get_tasks_percents() - {id задания: процент}
EnglishProgressService(student).get_modules_percents() - {id модуля: процент}
EnglishProgressService(student).get_course_percent() - процент курса

Три уровня, каждый считается из предыдущего:
-задание - правильные ответы / (шагов × 6 (REQUIRED_CORRECT_ANSWERS)) × 100,
не больше 100
-модуль - среднее процентов его заданий
-курс - среднее процентов модулей

Учитываются только задания:
-курса английского (settings.ENGLISH_COURSE_ID)
-активные (is_active = True)
-с хотя бы одним шагом
Задание без записи StudentProgress - 0%
Модуль без таких заданий в прогресс курса не входит

Округление:
-процент задания - round
-процент модуля и курса - вниз (//)

Данные загружаются один раз на экземпляр сервиса (2 запроса к БД):
-задания курса с количеством шагов и id модуля - ._get_tasks()
-правильные ответы студента по заданиям - ._get_correct_by_task()
Дальше все методы работают с ними в памяти,
поэтому для нескольких уровней на одной странице достаточно одного экземпляра

.get_task_percent() в БД не обращается,
его можно вызывать без загрузки заданий (как в TaskRunner)

Все методы возвращают int от 0 до 100
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
    REQUIRED_CORRECT_ANSWERS = {
        "words": 6,
        "sentences": 1,
    }
    
    def __init__(self, student: Student):
        self.student = student
        
        self.tasks = None
        self.correct_by_task = None
    
    @classmethod
    def get_required_correct_answers(
            cls, 
            task_type: str
        ) -> int:
        
        return cls.REQUIRED_CORRECT_ANSWERS.get(task_type, 1)
    
    def get_task_percent(
        self, 
        steps_count: int, 
        correct_count: int,
        task_type: str
    ) -> int:
        
        if steps_count == 0:
            return 0
        
        total = steps_count * self.get_required_correct_answers(task_type)
        # min для старіх шагов, на которіе студенті уже ответили 
        # до віпуска фикса багов в работе заданий "Слова"
        return min(100, round(correct_count / total * 100))
    
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
                steps_count=task.steps_count,
                task_type=task.type
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