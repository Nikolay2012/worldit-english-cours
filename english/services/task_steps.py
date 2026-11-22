"""
Сервис удаления всего списка слов задания

Используется эндпоинтом TaskStepsEndpoint,
когда в модалке списка слов нажимают «Видалити список» и подтверждают удаление

Использование:
TaskStepsService(task_id).delete_all()

Задание ищется сразу при создании сервиса (в __init__),
поэтому NotFoundError может подняться ещё до вызова .delete_all()

Что делает метод .delete_all():
-Проверяет, что на задание ещё не отвечали студенты - метод ._has_student_answers()
-Собирает имена файлов картинок задания до удаления записей
-Удаляет все шаги задания
вместе с ними (через CASCADE) удаляются Question, QuestionImage и AnswerOption
-После успешной транзакции удаляет файлы картинок из media - метод ._delete_files()

Категории слов (WordCategory) не удаляются, они общие для всех заданий

После удаления задание становится пустым,
и в него снова можно загрузить csv

Из ошибок, могут подниматься:
-NotFoundError - задание не найдено или не из курса английского
-ConflictError - на задание уже отвечали студенты
"""

from django.core.files.storage import default_storage
from django.db import transaction

from django.conf import settings
from english.models.english_task import EnglishTask
from english.models.question_image import QuestionImage
from english.services.exceptions import NotFoundError


class TaskStepsService:
    def __init__(self, task_id: int):
        self.task = self._get_task(task_id=task_id)
    
    def delete_all(self):
        
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
            self._delete_type_data()
            
            # Файлы удаляются только после успешного коммита
            # Если транзакция откатится, картинки останутся на месте
            transaction.on_commit(
                lambda: self._delete_files(image_names)
            )
            
    def _delete_files(self, image_names: list[str]):
        for name in image_names:
            default_storage.delete(name)
    
    def _get_task(self, task_id: int) -> EnglishTask:
        task = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не знайдено")
        
        return task
    
    # Метод, определяющий методы с дополнительной логикой удаления в конкретных типах заданий
    # К примеру: для задания 'предложения', помимо шагов задания, нужно удалять записи SentenceWordVariant,
    # в то время как для задания 'слова' этого делать не нужно
    def _delete_type_data(self):
        
        delete_methods = {
            "sentences": self._delete_sentence_word_variants
        }
        
        method = delete_methods.get(self.task.type)
        
        if method is not None:
            return method()
    
    def _delete_sentence_word_variants(self):
        
        self.task.word_variants.all().delete()
