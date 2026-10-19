from WorldIT import settings
from courses.models import Lesson
from english.models.english_task import EnglishTask
from english.services.exceptions import ValidationError, NotFoundError


def update_lesson_tasks(
        lesson_id: int, 
        renamed: list[dict[str, str]], 
        deleted: list[str]
    ):
    
    
    names = parse_names(renamed=renamed)
    deleted_ids = parse_ids(deleted=deleted)
    
    validate_names(names.values())
    
    lesson = get_lesson(lesson_id=lesson_id)
    lesson_tasks = get_lesson_tasks(
        lesson=lesson,
        # Объединяем списки с id переименованных и удаленных заданий
        task_ids=names.keys() | deleted_ids
    )
    
    rename_tasks(
        lesson_tasks=lesson_tasks,
        names=names
    )
    delete_tasks(
        lesson=lesson,
        deleted_ids=deleted_ids
    )

def parse_ids(deleted: list[str]) -> list[int]:
    
    try:
        deleted_ids = []
        
        for deleted_task_id in deleted:
            deleted_task_id: str
            
            deleted_ids.append(int(deleted_task_id))
        
        return deleted_ids
    
    except Exception as error:
        raise ValidationError("Некоректні id завдань")

def parse_names(
        renamed: list[dict[str, str]]
    ) -> dict[int, str]:
    
    try: 
        names = {}
        
        for renamed_task in renamed:
            renamed_task: dict
            
            id = int(renamed_task["taskId"])
            name = renamed_task["name"].strip()
            
            names[id] = name
        
        return names
    
    except Exception as error:
        raise ValidationError("Некоректні дані перейменування")

def validate_names(names: list[str]):
    
    for name in names:
        if not name:
            raise ValidationError("Назва завдання не може бути порожнью")
        
        # 100 - максимальна довжина назви завдання за замовчування
        if len(name) > 100:
            raise ValidationError("Назва завдання довша за 100 символів")

def get_lesson(lesson_id: int):
    
    lesson = Lesson.objects.filter(
        pk=lesson_id,
        module__course_id=settings.ENGLISH_COURSE_ID
    ).first()
    
    if lesson is None:
        raise NotFoundError("Урок не знайдено")
    
    return lesson

def get_lesson_tasks(
        lesson: Lesson, 
        task_ids: list
    ) -> list[EnglishTask]:
    
    tasks = list(EnglishTask.objects.filter(
        lesson=lesson,
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

def rename_tasks(
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

def delete_tasks(lesson: Lesson, deleted_ids: list[int]):
    
    EnglishTask.objects.filter(
        lesson=lesson,
        pk__in=deleted_ids
    ).delete()
