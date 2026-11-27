"""
Сервис создания и редактирования слов в задании типа "Слова"

Используется эндпоинтами:
-WordEndpoint - сохранение одного слова в модалке списка слов (после импорта CSV)
-WordsBatchEndpoint - сохранение всех изменений из боковой панели «Список слів»

Доступ к эндпоинтам - admin

Наследует WordImporter, откуда берёт создание шага со всеми записями,
сбор списка слов для клиента и константы (ANSWER_OPTIONS_COUNT, PLACEHOLDER_IMAGE)

У каждого слова два набора вариантов ответа (AnswerOption.language):
-uk - переводы, показываются, когда вопрос задан текстом (словом)
-en - английские слова, показываются, когда вопрос задан картинкой
В каждом наборе один правильный вариант и 5 неправильных,
взятых из других слов и переводов этого же задания

Создание слова - метод .create():
-Проверяет задание, категорию, слово, перевод и картинки
-Проверяет, что такого слова и такого перевода нет у других слов задания
(без учёта регистра)
-Проверяет, что в задании хватает других слов и переводов
для неправильных вариантов ответа (по 5 на каждый набор)
-Создаёт новый шаг в конце задания, вместе с Question, QuestionImage
и обоими наборами AnswerOption (uk и en)
-Если картинка не передана, она записывается как плейсхолдер

Редактирование слова - метод .update():
-Проверяет задание, шаг в этом задании, слово, перевод и картинки
-Проверяет, что такого слова и такого перевода нет у других слов задания
(кроме самого слова)
-Проверяет, что у слова есть правильный вариант перевода (uk)
-Обновляет текст вопроса
-Заменяет или удаляет картинки по их номеру (order)
-Если перевод изменился, обновляет правильный uk вариант слова
и неправильные uk варианты со старым переводом в других шагах задания
-Если слово изменилось, обновляет правильный en вариант слова
и неправильные en варианты со старым словом в других шагах задания

Сохранение пачки изменений - метод .save_batch():
-Получает изменения JSON-строкой (поле changes) и файлы картинок
-Каждое изменение - {"key", "mode", "step_id", "category", "word", "translation", "removed_images"}
-Картинки изменения приходят как image_<key>_<order>
-По mode вызывает .create() или .update() для каждого изменения
-Всё выполняется в одной транзакции: если хоть одно слово не прошло проверку,
не сохраняется ни одно
-В тексте ошибки указывается слово, на котором она возникла

Все записи в БД выполняются внутри транзакции
Старые файлы картинок удаляются из media только после успешной транзакции
(в .save_batch() - после успешного сохранения всей пачки)

.create() и .update() возвращают полный список слов задания по категориям
.save_batch() ничего не возвращает - клиент после сохранения перезагружает страницу

Из ошибок, могут подниматься:
-NotFoundError - задание, шаг или категория не найдены
-ValidationError - пустое слово или перевод, неверная картинка,
повторяющееся слово или перевод, не хватает слов или переводов для вариантов ответа,
повреждённые варианты ответа слова (нет правильного uk варианта)
или некорректные данные изменений в .save_batch()
"""

import io
import json

from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Max

from django.conf import settings
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
    
    def create(self, task_id: int, data, files) -> list[dict]:
        
        task = self._get_task(task_id=task_id)
        category = self._get_category(name=data.get("category", ""))
        word, translation = self._parse_word(data=data)
        
        images = self._parse_images(files=files)
        
        self._validate_unique_translation(
            task=task, 
            translation=translation
        )
        
        self._validate_unique_word(
            task=task,
            word=word
        )
        
        all_words = self._get_task_words(task=task)
        all_words.add(word)
        
        if len(all_words - {word}) < self.ANSWER_OPTIONS_COUNT -1: # отнимаем правильній ответ
            raise ValidationError(
                f"У завданні має бути щонайменше {self.ANSWER_OPTIONS_COUNT -1} інших слів"
            )
        
        # К уже имеющимся переводам добавляем новый
        all_translations = self._get_task_translations(task=task)
        all_translations.add(translation)
        
        if len(all_translations - {translation}) < self.ANSWER_OPTIONS_COUNT - 1:
            raise ValidationError(
                f"У завданні має бути щонайменше {self.ANSWER_OPTIONS_COUNT - 1} інших перекладів"
            )
        
        # Получаем порядковый номер последнего шага
        max_order = task.steps.aggregate(Max("order"))["order__max"]
        # Создаём порядковый номер для нового шага
        # Если шагов не было - то 0
        # Если были, то к полученному выше max_order прибавляем 1
        order = 0 if max_order is None else max_order + 1
        
        with transaction.atomic():
            # Внутри транзакции запускаем создание EnglishTaskStep
            # Метод ._create_word_step() унаследован из WordImporter
            # А в самом же методе ._create_word_step(), 
            # выполняется создание группы записей моделей Question, QuestionImage, AnswerOption
            # По этому внутри транзакции
            self._create_word_step(
                task=task,
                order=order,
                row={
                    "word": word,
                    "translation": translation,
                    "image_1": "",
                    "image_2": ""
                },
                category=category,
                all_words=all_words,
                all_translations=all_translations,
                image_files=(images.get(0), images.get(1))
            )
        
        # Возвращаем полный список слов задания
        # Ипользуется метод ._get_words_list(), 
        # который создан в родительском WordImporter
        return self._get_words_list(task=task)
    
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
        self._validate_unique_word(
            task=task, 
            word=word, 
            exclude_step=step
        )
        
        question: Question = step.question
        correct_answer_option: AnswerOption | None = question.options.filter(
            is_correct=True,
            language="uk"
        ).first()
        
        if correct_answer_option is None:
            raise ValidationError(
                "Варіанти відповіді цього слова пошкоджені або відсутні"
            )
        
        old_translation = correct_answer_option.text
        old_word = question.text
        
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
                    language="uk",
                    text=old_translation
                ).update(text=translation)
            
            if word != old_word:
                question.options.filter(
                    is_correct=True,
                    language="en"
                ).update(text=word)
                
                AnswerOption.objects.filter(
                    question__step__task=task,
                    language="en",
                    is_correct=False,
                    text=old_word
                ).update(text=word)
            
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
            text__iexact=translation,
            language="uk"
        )
        
        if exclude_step is not None:
            options = options.exclude(question__step=exclude_step)
            
        if options.exists():
            raise ValidationError("Такий переклад вже є в іншого слова")
    
    def _validate_unique_word(
            self,
            task: EnglishTask,
            word: str,
            exclude_step: EnglishTaskStep | None = None
        ):
        
        questions = Question.objects.filter(
            step__task=task,
            text__iexact=word
        )
        
        if exclude_step is not None:
            questions = questions.exclude(
                step=exclude_step)
            
        if questions.exists():
            raise ValidationError(
                "Таке слово вже є в цьому завданні")
    
    def _get_task_words(self, task: EnglishTask):
        
        return set(
            Question.objects.filter(step__task=task).values_list("text", flat=True)
        )
    
    def _get_task_translations(self, task: EnglishTask) -> set[str]:
        
        return set(
            AnswerOption.objects.filter(
                question__step__task=task,
                language="uk",
                is_correct=True
            ).values_list("text", flat=True)
        )
    
    # Удаляем с медиа
    def _delete_files(self, names: list[str]):
        
        for name in names:
            default_storage.delete(name)
    
    def save_batch(
            self, 
            task_id: int, 
            changes_json: str, 
            files
        ):
        
        try:
            changes = json.loads(changes_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValidationError("Некоректні дані змін") from error
        
        with transaction.atomic():
            for change in changes:
                key = change.get("key")
                
                data = {
                    "word": change.get("word", ""),
                    "translation": change.get("translation", ""),
                    "category": change.get("category") or ""
                }
                
                for order in change.get("removed_images", []):
                    data[f"remove_image_{order}"] = "1"
                    
                item_files = {}
                
                for order in range(self.IMAGES_COUNT):
                    file = files.get(f"image_{key}_{order}")
                    
                    if file is not None:
                        item_files[f"image_{order}"] = file
                        
                try:
                    if change.get("mode") == "create":
                        self.create(task_id=task_id, data=data, files=item_files)
                    else:
                        self.update(
                            task_id=task_id,
                            step_id=change.get("step_id"),
                            data=data,
                            files=item_files
                        )
                except ValidationError as error:
                    raise ValidationError(
                        f"«{data['word']}»: {error.message}"
                    ) from error
