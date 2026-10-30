"""
Реестр импортёров заданий из csv

Выбирает импортёр по типу задания (поле type у EnglishTask)
Используется эндпоинтом TaskImportEndpoint

Использование:
TaskImportersRegistry().get_task_importer(task_id).import_file(task_id, file)

Что делает метод .get_task_importer():
-Получает тип задания по task_id (только задания курса английского)
-Находит класс импортёра для этого типа в TASK_IMPORTERS
-Возвращает объект импортёра

Чтобы добавить импорт для нового типа задания,
достаточно добавить его импортёр в TASK_IMPORTERS

Из ошибок, могут подниматься:
-NotFoundError - задание не найдено или не из курса английского
-ValidationError - для типа задания нет импортёра
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
