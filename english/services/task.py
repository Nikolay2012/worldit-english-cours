"""
Сервис для проверок одного задания английского курса

Задание передаётся в сервис при создании,
дальше все методы работают с ним
Сервис только проверяет, данные он не изменяет

Использование:
service = EnglishTaskService(task)
service.can_access(student) - может ли студент открыть задание
service.has_steps() - есть ли у задания шаги

Студент может открыть задание, если:
-у задания есть шаги (пустое задание студенту не показывается)
-задание не в архиве (is_active = True)
-задание доступно (is_available = True)
-задание открыто этому студенту (есть запись OpenEnglishTask) - метод ._is_opened_for()

Роли сервис не проверяет,
персонал (admin) видит все задания, и это решает view
"""

from english.models import EnglishTask, OpenEnglishTask
from users.models import Student


class EnglishTaskService:
    def __init__(self, task: EnglishTask):
        self.task = task
    
    def can_access(self, student: Student) -> bool:
        
        if not self.has_steps():
            return False
        
        return self.task.is_active and self.task.is_available and self._is_opened_for(student)
    
    def has_steps(self):
        return self.task.steps.exists()
    
    def _is_opened_for(self, student: Student) -> bool:
        return OpenEnglishTask.objects.filter(
            task=self.task,
            student=student,
        ).exists()
