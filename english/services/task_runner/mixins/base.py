from typing import TYPE_CHECKING

from django.db.models import QuerySet


if TYPE_CHECKING:
    from english.models.english_task import EnglishTask
    from english.models.english_task_step import EnglishTaskStep
    from english.models.student_progress import StudentProgress
    from users.models import CustomUser, Student


class TaskRunnerBase:
    """
    Класс-заглушка только для типизации (TYPE_CHECKING)
    В работе приложения не используется
    
    Даёт миксинам TaskRunner подсказки по атрибутам и методам,
    которые на самом деле объявлены в TaskRunner
    
    Реальные значения атрибутов устанавливаются в TaskRunner.__init__()
    """
    
    if TYPE_CHECKING:
        
        user: "CustomUser"
        task: "EnglishTask"
        student: "Student | None"
        
        STAFF_TYPES: list[str]
        REQUIRED_CORRECT_ANSWERS: int
        
        # TaskRunner
        def _is_staff(self) -> bool: ...
        def _get_steps(self) -> QuerySet["EnglishTaskStep"]: ...
        def _get_progress_record(self) -> "StudentProgress": ...
        def _get_correct_by_step(self) -> dict[int, int]: ...
        def _get_last_answered_step_id(self) -> int | None: ...
        def _get_student_progress(
            self,
            steps_count: int,
            progress: "StudentProgress"
        ) -> dict: ...
