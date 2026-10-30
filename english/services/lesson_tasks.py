"""
Сервис изменения заданий урока

Используется эндпоинтом LessonTasksEndpoint,
когда урок сохраняется после режима редактирования
За один запрос переименовывает и удаляет задания одного урока

Использование:
LessonTasksService(lesson_id, deleted=[...], renamed=[...]).update()

Данные приходят от клиента в таком виде:
-renamed - [{"taskId": "12", "name": "Нова назва"}, ...]
-deleted - ["15", "16"]

Что делает метод .update(), по порядку:
-Переводит id и названия из строк в нужные типы - методы ._parse_ids() и ._parse_names()
-Проверяет названия: не пустые и не длиннее 100 символов - метод ._validate_names()
-Проверяет, что все задания есть в этом уроке - метод ._get_lesson_tasks()
-Переименовывает задания одним запросом через bulk_update - метод ._rename_tasks()
-Удаляет задания - метод ._delete_tasks()

Урок ищется сразу при создании сервиса (в __init__),
поэтому NotFoundError может подняться ещё до вызова .update()

Из ошибок, могут подниматься:
-NotFoundError - урок не найден, или часть заданий не из этого урока
-ValidationError - некорректные id или названия

Сервис ничего не знает про HTTP,
статусы ответа выставляет эндпоинт
"""

from django.core.files.storage import default_storage
from django.db import transaction

from WorldIT import settings
from courses.models import Lesson
from english.models.english_task import EnglishTask
from english.models.question_image import QuestionImage
from english.services.exceptions import ValidationError, NotFoundError


class LessonTasksService:
    def __init__(
            self, 
            lesson_id: int,
            deleted: list[str], 
            renamed: list[dict[str, str]]
        ):
        
        self.lesson = self._get_lesson(lesson_id=lesson_id)
        self.deleted = deleted
        self.renamed = renamed
        
    
    def update(self):
        
        names = self._parse_names()
        deleted_ids = self._parse_ids()
        
        self._validate_names(names.values())
        
        lesson_tasks = self._get_lesson_tasks(
            # Объединяем списки с id переименованных и удаленных заданий
            task_ids=names.keys() | deleted_ids
        )
        
        self._rename_tasks(
            lesson_tasks=lesson_tasks,
            names=names
        )
        self._delete_tasks(
            deleted_ids=deleted_ids
        )
    
    def _parse_ids(self) -> list[int]:
        
        try:
            deleted_ids = []
            
            for deleted_task_id in self.deleted:
                deleted_task_id: str
                
                deleted_ids.append(int(deleted_task_id))
            
            return deleted_ids
        
        except Exception as error:
            raise ValidationError("Некоректні id завдань")
    
    def _parse_names(self) -> dict[int, str]:
        
        try: 
            names = {}
            
            for renamed_task in self.renamed:
                renamed_task: dict
                
                id = int(renamed_task["taskId"])
                name = renamed_task["name"].strip()
                
                names[id] = name
            
            return names
        
        except Exception as error:
            raise ValidationError("Некоректні дані перейменування")
    
    def _validate_names(self, names: list[str]):
        
        for name in names:
            if not name:
                raise ValidationError("Назва завдання не може бути порожнью")
            
            # 100 - максимальна довжина назви завдання за замовчування
            if len(name) > 100:
                raise ValidationError("Назва завдання довша за 100 символів")
    
    def _get_lesson(self, lesson_id: int):
        
        lesson = Lesson.objects.filter(
            pk=lesson_id,
            module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if lesson is None:
            raise NotFoundError("Урок не знайдено")
        
        return lesson

    def _get_lesson_tasks(
            self,
            task_ids: list
        ) -> list[EnglishTask]:
        
        tasks = list(EnglishTask.objects.filter(
            lesson=self.lesson,
            pk__in=task_ids
        ))
        
        # Проверяем наличие отредактированных заданий в уроке
        # в противном случае будет кастомный NotFoundError
        recieved_task_ids_set = {task.pk for task in tasks}
        edited_task_ids_set = set(task_ids)
        
        is_missing_ids = edited_task_ids_set - recieved_task_ids_set
        
        if is_missing_ids:
            raise NotFoundError(
                "Деякі завдання не були знайдені в цьому уроці"
            )
        
        return tasks

    def _rename_tasks(
            self,
            lesson_tasks: list[EnglishTask],
            names: dict[int, str]
        ):
        
        changed_tasks = []
        
        for task in lesson_tasks:
            task: EnglishTask
            
            new_name = names.get(task.pk)
            
            if new_name and new_name != task.name:
                task.name = new_name
                changed_tasks.append(task)
        
        EnglishTask.objects.bulk_update(changed_tasks, ["name"])

    def _delete_tasks(self, deleted_ids: list[int]):
        
        image_names = list(
            QuestionImage.objects.filter(
                question__step__task__lesson=self.lesson,
                question__step__task_id__in=deleted_ids
            ).exclude(
                image__isnull=True
            ).exclude(
                image=""
            # flat=true для получения конкретно значений, а не кортежей
            ).values_list("image", flat=True)
        )
        
        with transaction.atomic():
            EnglishTask.objects.filter(
                lesson=self.lesson,
                pk__in=deleted_ids
            ).delete()
            
            transaction.on_commit(
                lambda: self._delete_files(image_names=image_names)
            )
    
    def _delete_files(self, image_names: list[str]):
        
        for name in image_names:
            default_storage.delete(name)
