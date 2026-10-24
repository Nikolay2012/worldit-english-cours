"""
Сервис операций над одним заданием английского курса.

Контекст сервиса — конкретное задание, передаётся в конструктор.
Методы отвечают на вопросы о задании и не изменяют данные.

Использование:
    service = EnglishTaskService(task)
    service.can_access(student)   # может ли студент открыть задание
    service.has_steps()           # есть ли у задания шаги

Правило доступа студента:
    задание открыто для всех (is_available = True)
    и выдано этому студенту (есть запись OpenEnglishTask).

Проверку ролей (админ, ментор) сервис не выполняет:
    персонал видит все задания, и это решает view.
"""

from english.models import EnglishTask, OpenEnglishTask
from users.models import Student


class EnglishTaskService:

    def __init__(self, task: EnglishTask):
        self.task = task

    def can_access(self, student: Student) -> bool:
        return self.task.is_available and self._is_opened_for(student)

    def has_steps(self):
        return self.task.steps.exists()
    
    def _is_opened_for(self, student: Student) -> bool:
        return OpenEnglishTask.objects.filter(
            task=self.task,
            student=student,
        ).exists()
