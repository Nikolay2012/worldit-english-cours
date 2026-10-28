"""

"""

import io

from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from WorldIT import settings
from english.models.answer_option import AnswerOption
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.models.question import Question
from english.models.word_category import WordCategory
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_importers.word import WordImporter


class WordStepService(WordImporter):
    def __init__(self):
        super().__init__()
        
        # Макс размер изображения 2 МБ
        self.MAX_IMAGE_SIZE = 2 * 1024 * 1024
        
        # Форматы указываем в кортеже
        # Ибо endswith не принимает список []
        self.IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
        
        # Всего две картинки (QuestionImage) для одного вопроса
        self.IMAGES_COUNT = 2
    
    def create(self, task_id: int, data, files):
        pass
    
    def update(
            self, 
            task_id: int, 
            step_id: int, 
            data, 
            files
        ) -> list[dict]:
        
        task = self._get_task(task_id=task_id)
        step = self._get_step(task=task, step_id=step_id)
        word, translation = self._parse_word(data=data)
        
        
        images = self._parse_images(files=files)
        
        # Номера удаленніх изображений
        removed_orders = self._parse_removed_images(data=data)
        
        self._validate_unique_translation(
            task=task, 
            translation=translation, 
            exclude_step=step
        )
        
        question: Question = step.question
        correct_answer_option: AnswerOption = question.options.get(
            is_correct=True
        )
        old_translation = correct_answer_option.text
        
        old_image_files = []
        
        with transaction.atomic():
            question.text = word
            question.save()
            
            for question_image in question.images.all():
                question_image_order = question_image.order
                
                if question_image_order in images.keys():
                    if question_image.image:
                        old_image_files.append(
                            question_image.image.name
                        )
                    
                    question_image.image.save(
                        f"{question.text}_{question_image_order}.png",
                        images[question_image_order],
                        save=False # сохраним всё вместе ниже
                    )
                    question_image.is_placeholder = False
                    question_image.source_url = ""
                    question_image.save()
                    
                elif question_image_order in removed_orders:
                    if question_image.image:
                        old_image_files.append(
                            question_image.image.name
                        )
                    
                    question_image.image = None
                    question_image.is_placeholder = True
                    question_image.source_url = ""
                    question_image.save()
            
            # Не записываем совпадающий перевод
            if translation != old_translation:
                # Важный кусок обнволения, потому немного контекста:
                # На каждый Question создаётся 6 AnswerOption-ов
                # В этих AnswerOption's может быть перевод, который был обновлен
                # В задании, где обновленный перевод является правильным ответом, 
                # он будет с is_correct=True
                # Прямо тут, этот правильный перевод и обновляется
                correct_answer_option.text = translation
                correct_answer_option.save()
                
                # Но этот перевод есть и в других шагах заданий (EnglishTaskStep), 
                # где он является одним из 6-ти AnswerOption-ов
                # И там этот перевод нужно тоже обновить
                # Но в других заданиях, этот перевод уже будет одним из НЕправильных ответов
                # Именно по этому, в фильтре указан is_correct=False
                AnswerOption.objects.filter(
                    question__step__task=task,
                    is_correct=False,
                    text=old_translation
                ).update(text=translation)
            
            # Удаляем старые файлы из медиа
            transaction.on_commit(
                lambda: self._delete_files(old_image_files)
            )
        
        # Возвращаем полный список слов задания
        # Ипользуется метод ._get_words_list(), 
        # который создан в родительском WordImporter
        return self._get_words_list(task=task)
    
    def _get_task(self, task_id: int) -> EnglishTask:
        
        task = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не знайдено")
        
        return task
    
    def _get_step(self, task: EnglishTask, step_id: int) -> EnglishTaskStep:
        
        step = EnglishTaskStep.objects.filter(
            pk=step_id,
            task=task
        ).select_related("question").first()
        
        if step is None:
            raise NotFoundError("Слово не знайдено в цьому завданні")
        
        return step
    
    def _get_category(self, name: str) -> WordCategory:
        
        category = WordCategory.objects.filter(
            name=name.strip().lower()
        ).first()
        
        if category is None:
            raise NotFoundError("Категорію не знайдено")
        
        return category
    
    def _parse_word(self, data) -> tuple[str, str]:
        
        word = data.get("word", "").strip()
        translation = data.get("translation", "").strip()
        
        if not word:
            raise ValidationError("Слово не може бути порожнім")
        
        if not translation:
            raise ValidationError("Переклад не може бути порожнім")
        
        return word, translation
    
    def _parse_images(self, files) -> dict[int, UploadedFile]:
        
        images = {}
        
        for order in range(self.IMAGES_COUNT):
            file = files.get(f"image_{order}")
            
            if file is None:
                continue
            
            self._validate_image(file=file, order=order)
            images[order] = file
        
        return images
    
    def _parse_removed_images(self, data) -> set[int]:
        
        removed_orders = set()
        
        for order in range(self.IMAGES_COUNT):
            if data.get(f"remove_image_{order}") == "1":
                removed_orders.add(order)
        
        return removed_orders
    
    def _validate_image(self, file: UploadedFile, order: int):
        
        image_number = order + 1
        
        if not file.name.lower().endswith(self.IMAGE_EXTENSIONS):
            raise ValidationError(
                f"Зображення {image_number} повинно мати формат .png, .jpg або .jpeg"
            )
        
        if file.size > self.MAX_IMAGE_SIZE:
            raise ValidationError(
                f"Розмір зображення {image_number} має бути до 2 МБ"
            )
        
        try:
            # Проверка на то, что сказанные байты являются изображением
            # через pil удобнее
            # Если возникнет ошибка, нижележащее исключение 
            # сообщит об єтом
            Image.open(io.BytesIO(file.read())).verify()
        except Exception as error:
            raise ValidationError(f"Зображення {image_number} пошкоджено") from error
        
        # После работы pillow, возвращаем курсор в начало файла
        file.seek(0)
    
    def _validate_unique_translation(
            self,
            task: EnglishTask,
            translation: str,
            exclude_step: EnglishTaskStep | None = None
        ):
        
        options = AnswerOption.objects.filter(
            question__step__task=task,
            is_correct=True,
            text__iexact=translation
        )
        
        if exclude_step is not None:
            options = options.exclude(question__step=exclude_step)
            
        if options.exists():
            raise ValidationError("Такий переклад вже є в іншого слова")
    
    def _get_task_translations(self, task: EnglishTask) -> set[str]:
        
        return set(
            AnswerOption.objects.filter(
                question__step__task=task,
                is_correct=True
            ).values_list("text", flat=True)
        )
    
    # Удаляем с медиа
    def _delete_files(self, names: list[str]):
        
        for name in names:
            default_storage.delete(name)
