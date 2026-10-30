"""

"""

from django.conf import settings

from english.models.english_task import EnglishTask
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_importers.base import BaseEnglishTaskImporter
from english.services.task_importers.word import WordImporter


class TaskImportersRegistry:
    def __init__(self):
        
        self.TASK_IMPORTERS = {
            "words": WordImporter,
        }
    
    def get_task_importer(self, task_id: int) -> BaseEnglishTaskImporter:
        
        task_type = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).values_list("type", flat=True).first()
        
        if task_type is None:
            raise NotFoundError("Завдання не знайдено")
        
        importer_class = self.TASK_IMPORTERS.get(task_type)
        
        if importer_class is None:
            raise ValidationError("Для цього типу завдання імпорт не підтримується")
        
        return importer_class()
