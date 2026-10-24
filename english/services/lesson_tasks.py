"""
Сервис изменения заданий урока.

Используется эндпоинтом LessonTasksEndpoint при сохранении урока
в режиме редактирования: переименовывает и удаляет задания одного урока
за одну операцию.

Использование:
    LessonTasksService(lesson_id, deleted=[...], renamed=[...]).update()

Входные данные (как пришли от клиента):
    renamed — [{"taskId": "12", "name": "Нова назва"}, ...]
    deleted — ["15", "16"]

Порядок работы update():
    1. Разбор id и названий в типы Python
    2. Проверка названий: не пустые, не длиннее 100 символов
    3. Проверка, что все задания принадлежат этому уроку
    4. Переименование (bulk_update)
    5. Удаление

Исключения:
    NotFoundError    — урок не найден (уже в конструкторе)
    или часть заданий не принадлежит уроку
    ValidationError  — некорректные id или названия

Сервис не знает об HTTP: статусы ответов определяет эндпоинт.
"""

from WorldIT import settings
from courses.models import Lesson
from english.models.english_task import EnglishTask
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
        
        EnglishTask.objects.filter(
            lesson=self.lesson,
            pk__in=deleted_ids
        ).delete()
