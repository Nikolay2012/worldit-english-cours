"""

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
