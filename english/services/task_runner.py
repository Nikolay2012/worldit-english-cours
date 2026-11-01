"""

"""

from django.db.models import QuerySet

from WorldIT import settings
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.services.exceptions import NotFoundError
from english.services.step_handlers.registry import StepHandlerRegistry
from users.models import CustomUser


class TaskRunner:
    def __init__(self, task_id: int, user: CustomUser):
        
        self.user = user
        self.task = self._get_task(task_id=task_id)
        
        #  типы персонала (админа и ментора)
        # отдельно вынесены, по причине отличной от студента логики записи прогресса 
        # (прогресс у них отсутствует)
        self.STAFF_TYPES = ["admin", "mentor"]
        
    def get_next_step(
            self, 
            after_step_id: int | None = None
        ) -> dict:
        
        if self._is_staff():
            step, progress = self._get_staff_next_step(
                after_step_id=after_step_id)
        else:
            step, progress = self._get_student_next_step(
                after_step_id=after_step_id
            )
        
        return {
            "step": self._get_step_data(step=step) if step else None,
            "progress": progress
        }
    
    def _get_staff_next_step(
            self, 
            after_step_id: int | None
        ) -> tuple:
        
        steps: QuerySet[EnglishTaskStep] = self._get_steps()
        
        if after_step_id is None:
            step = steps.first()
        else:
            after_step: EnglishTaskStep = steps.filter(pk=after_step_id).first()
            
            if after_step is None:
                return NotFoundError(
                    "Крок не знайдено в цьому завданні"
                )
            
            step = steps.filter(order__gt=after_step.order).first()
        
        return step, self._get_staff_progress(
            steps=steps,
            step=step
        )
    
    def _get_student_next_step(
            self, 
            after_step_id: int | None
        ) -> tuple:
        
        # Пока так, логику прохождения студентом буду дальше дописывать
        return self._get_staff_next_step(after_step_id=after_step_id)
    
    def _get_staff_progress(
            self, 
            steps: QuerySet[EnglishTaskStep], 
            step: EnglishTaskStep | None
        ) -> dict:
        
        # Если следующего шага нету, то задание пройдено
        # соответстенно 100%
        if step is None:
            return {
                "percent": 100,
                "is_completed": True
            }
        
        # В случае же, если следующий шаг есть
        # Определяем общее количестве шагов, и сколько было пройдено
        # Отталкиваясь от этого получаем процент прохождения задания
        total_steps_count = steps.count()
        completed_steps_count = steps.filter(order__lt=step.order).count()
        
        return {
            "percent": round(completed_steps_count / total_steps_count * 100),
            "is_completed": False
        }
    
    def _get_steps(self):
        
        return self.task.steps.select_related(
            "question"
        ).prefetch_related(
            "question__options",
            "question__images"
        ).order_by("order")
    
    def _get_step_data(self, step: EnglishTaskStep) -> dict:
        
        handler = StepHandlerRegistry().get_handler(
            kind=step.kind
        )
        
        return handler.get_step_data(step=step)
    
    def _is_staff(self) -> bool:
        
        account_types = self.user.account_types
        
        for staff_type in self.STAFF_TYPES:
            if staff_type in account_types:
                return True
            
        return False
    
    def _get_task(self, task_id: int) -> EnglishTask:
        
        task = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не знайдено")
        
        return task
