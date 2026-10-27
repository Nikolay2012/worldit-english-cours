import random

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Prefetch
from django.templatetags.static import static
from django.db import transaction

from english.models.answer_option import AnswerOption
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.models.question import Question
from english.models.question_image import QuestionImage
from english.models.word_category import WordCategory
from english.services.exceptions import ValidationError
from english.services.task_importers.base import BaseEnglishTaskImporter
from english.services.image_downloader import ImageDownloader


class WordImporter(BaseEnglishTaskImporter):
    def __init__(self):
        
        # Указываем свои "местные" названия столбцов
        # Таким образом заменяем стандартные столбцы из самого csv файла в которых, 
        # например может быть BOM-метка, которая приведет к поднятию лишних исключений при парсинге
        self.COLUMNS = ["word", "translation", "category", "image_1", "image_2"]
        
        # Обязательные столбцы, без которых создание шагов и вопросов невозможно в принципе
        self.REQUIRED_COLUMNS = ["word", "translation", "category"]
        
        # Количество вариантов ответа в задании типа "Слова"
        # Взято из дизайн-проекта
        self.ANSWER_OPTIONS_COUNT = 6
        
        self.PLACEHOLDER_IMAGE = "english/questions_placeholder/question_placeholder.png"
    
    def import_file(
            self, 
            task_id: int, 
            file: UploadedFile
        ) -> list[dict[str, str]]:
        
        task, rows = super().import_file(
            task_id=task_id,
            file=file
        )
        
        # Переводы уникальные (set())
        all_translations = set()
        
        for row in rows:
            all_translations.add(row["translation"])
        
        if len(all_translations) < self.ANSWER_OPTIONS_COUNT:
            raise ValidationError(f"У файлі має бути щонайменше {self.ANSWER_OPTIONS_COUNT} різних перекладів")
        
        # Изображения
        urls = {}

        for order, row in enumerate(rows):
            urls[(order, 0)] = row["image_1"]
            urls[(order, 1)] = row["image_2"]
        
        images_data = ImageDownloader().download_images(
            urls=urls
        )
        
        # Последующие действия с записью данных задания выполняем внутри транзакции
        # По разным причинам, если не удалось, например, 
        # записать один из вопросов задания - тогда вся запись задания некорректна
        # По понятным причинам это решение лучше чем оставлять частично записанное задание
        with transaction.atomic():
            # Категории
            categories = self._get_or_create_categories(rows=rows)
            
            # Создание шагов, вопросов, изображений вопросов и вариантов ответа
            for order, row in enumerate(rows):
                self._create_word_step(
                    task=task,
                    order=order,
                    row=row,
                    category=categories[row["category"]],
                    all_translations=all_translations,
                    image_files=(
                        images_data[(order, 0)], # зображення 1
                        images_data[(order, 1)] # Та зображення 2 соответственно
                    )
                )
        
        return self._get_words_list(task=task)
    
    def _get_words_list(self, task: EnglishTask) -> list[dict]:
        """
        Метод, возвращающий все данные необходимые 
        клиенту после парсинга csv со словами
        """
        
        steps = task.steps.select_related(
            "category", 
            "question"
        ).prefetch_related(
            Prefetch("question__options", queryset=AnswerOption.objects.order_by("order")),
            Prefetch("question__images", queryset=QuestionImage.objects.order_by("order"))
        ).order_by("order")
        
        # категории групп, на в дизайне: «Диеслова», «Займенники», «Именники» и др.
        categories_groups = {}
        
        for step in steps:
            category_name = step.category.name
            
            if category_name not in categories_groups.keys():
                categories_groups[category_name] = []
            
            categories_groups[category_name].append(
                self._serialize_word(step=step)
            )
        
        result = []
        
        for category_name, words in categories_groups.items():
            result.append({
                "category": category_name,
                "words": words
            })
        
        return result
    
    def _serialize_word(self, step: EnglishTaskStep) -> dict:
        
        question = step.question
        options = list(question.options.all())
        correct = next((option for option in options if option.is_correct), None)

        return {
            "step_id": step.id,
            "category": step.category.name,
            "question": {
                "id": question.id,
                "text": question.text,
                "allows_multiple": question.allows_multiple,
            },
            "translation": correct.text if correct else "",
            "options": [self._serialize_option(option) for option in options],
            "images": [self._serialize_image(image) for image in question.images.all()],
        }
    
    def _serialize_option(self, option: AnswerOption) -> dict:
        return {
            "id": option.id,
            "text": option.text,
            "is_correct": option.is_correct,
            "order": option.order,
        }

    def _serialize_image(self, image: QuestionImage) -> dict:
        return {
            "id": image.id,
            "order": image.order,
            "url": image.image.url if image.image else static(self.PLACEHOLDER_IMAGE),
            "is_placeholder": image.is_placeholder,
            "source_url": image.source_url,
        }
    
    def _create_word_step(
            self,
            task: EnglishTask,
            order: int,
            row: dict[str, str],
            category: WordCategory,
            all_translations: set[str],
            image_files: tuple
        ):
        """
        Метод создания шага задания, и всех связанных записей:
        -Вопроса (модель Question) - здесь, в этом методе
        -Варианта ответа (AnswerOption) - метод ._create_answer_options()
        -Изображения (QuestionImage) - метод ._create_question_images()
        """
        
        step = EnglishTaskStep.objects.create(
            task=task,
            kind="question",
            order=order,
            category=category
        )
        
        question = Question.objects.create(
            step=step,
            text=row["word"],
            allows_multiple=False # пока что, будет только False
        )
        
        self._create_answer_options(
            question=question,
            correct=row["translation"],
            all_translations=all_translations
        )
        
        self._create_question_images(
            question=question,
            row=row,
            image_files=image_files
        )
    
    def _create_answer_options(
            self,
            question: Question,
            correct: str,
            all_translations: set[str]
        ):
        
        # {correct} - специально оборачиваем правильный вариант ответа в множество
        # для возможности удаления правильного варианта ответа из выборки
        wrong_options = list(all_translations - {correct})
        
        wrong_options_after_sample = random.sample(
            wrong_options,
            self.ANSWER_OPTIONS_COUNT -1 # -1 - один правильный ответ, оставшиеся 5 - неправильные
        )
        
        
        options = [
            (correct, True)
        ]
        
        for text in wrong_options_after_sample:
            options.append(
                (text, False)
            )
        
        # Сервер перемешивает неправильный варианты ответа
        # Именно сервер, чтобы нельзя было корректировать порядок вопросов
        # путём вмешательства в работу JS клиента со стороны пользователя
        random.shuffle(options)
        
        for option_order, (text, is_correct) in enumerate(options):
            AnswerOption.objects.create(
                question=question,
                is_correct=is_correct,
                text=text,
                order=option_order
            )
    
    def _create_question_images(
            self,
            question: Question,
            row: dict[str, str],
            image_files: tuple
        ):
        
        for img_index, file in enumerate(image_files):
            # Отдельно запишем файла
            # с еще одной проверкой
            question_image = QuestionImage(
                source_url=row[f"image_{img_index +1}"],
                order=img_index,
                is_placeholder=True if file is None else False,
                question=question,
            )
            
            if file is not None:
                question_image.image.save(
                    f"{question.text}_{img_index}.png",
                    file,
                    # Отдельно сохраним через save
                    # всю инфу сразу
                    save=False
                )
            
            question_image.save()
    
    def _parse_row(
            self, 
            row: list[str], 
            line_num: int
        ) -> dict[str, str]:
        """
        Парс конкретного ряда вынесен в отдельный метод,
        по причине нахождения здесь свойственных только рядок проверок
        
        line_num передан для удобного вывода ряда, 
        на котором csv.reader находится при выводе ошибки
        
        Из ошибок, может подниматься ValidationError
        """
        
        # Пустой ли ряд
        if not any(cell.strip() for cell in row):
            raise ValidationError(f"Рядок {line_num}: порожній рядок")
        
        # Ряды должны быть одной длины
        # В противном случае zip() не запишет часть информации
        # Это приведет к поднятию лишних исключений уже при работе заданий
        if len(row) != len(self.COLUMNS):
            raise ValidationError(f"Рядок {line_num}: рядок має бути довжини {len(self.COLUMNS)}")
        
        data = {}
        
        for column, cell in zip(self.COLUMNS, row):
            data[column] = cell.strip()
        
        for column in self.REQUIRED_COLUMNS:
            # Проверяем, заполнена ли клетка в ряду
            # Если даже одна клетка не заполнена - весь csv не принимается
            if not data[column]:
                raise ValidationError(f"Рядок {line_num}: не заповнене поле «{column}»")
        
        data["category"] = data["category"].lower()
        
        return data
    
    def _get_or_create_categories(
        self, 
        rows: list[dict[str, str]]
    ) -> dict[str, WordCategory]:
        
        # set, нужны уникальные имена категорий без повторов
        categories_names = set()
        
        for row in rows:
            categories_names.add(row["category"])
        
        categories = {}
        
        for name in categories_names:
            category, _ = WordCategory.objects.get_or_create(
                name=name
            )
            categories[name] = category
        
        return categories
