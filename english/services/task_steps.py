"""

"""

from django.core.files.storage import default_storage
from django.db import transaction

from WorldIT import settings
from english.models.english_task import EnglishTask
from english.models.question_image import QuestionImage
from english.services.exceptions import ConflictError, NotFoundError


class TaskStepsService:
    def __init__(self, task_id: int):
        self.task = self._get_task(task_id=task_id)
    
    def delete_all(self):
        
        # Если на задание уже отвечали - список не удаляем,
        # иначе пропадёт прогресс студентов
        if self._has_student_answers():
            raise ConflictError("Студенти вже відповідали на це завдання")
        
        # Имена файлов собираем ДО удаления,
        # после delete() записей QuestionImage уже не будет
        image_names = list(
            QuestionImage.objects.filter(
                question__step__task=self.task
            ).exclude(
                image__isnull=True
            ).exclude(
                image=""
            ).values_list("image", flat=True)
        )
        
        with transaction.atomic():
            self.task.steps.all().delete()
            
            # Файлы удаляются только после успешного коммита
            # Если транзакция откатится, картинки останутся на месте
            transaction.on_commit(
                lambda: self._delete_files(image_names)
            )
            
    def _delete_files(self, image_names: list[str]):
        for name in image_names:
            default_storage.delete(name)
    
    # Пока метод пустой
    # будет заполнен с настройкой прогресса студентов в прохождении заданий
    def _has_student_answers(self) -> bool:
        return False
    
    def _get_task(self, task_id: int) -> EnglishTask:
        task = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не знайдено")
        
        return task
