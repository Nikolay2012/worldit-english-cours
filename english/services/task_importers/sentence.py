"""
Импортёр задания типа "Речення" из двух csv файлов

Ядро импорта: разбор файла предложений и общий порядок импорта
Остальное вынесено в миксины:
-SentenceMixin - создание шага с предложением, сбор списка предложений для клиента
-SentenceWordVariantMixin - разбор и запись файла "Слова для речень"

Наследует BaseEnglishTaskImporter, откуда берёт получение пустого задания
и чтение файла (кодировка, размер, расширение)

Наследуется SentenceStepService, который использует отсюда
разбор предложения, регистр первого слова, создание шага с токенами,
сбор списка предложений и константы

Используется SentenceHandler (прохождение и боковая панель):
-константы GAP_MARKER, ZERO_ARTICLE, I_FORMS
-._serialize_sentence() - данные предложения для боковой панели (.get_list_item())

Файлы (из модалки загрузки):
-file - предложения
-variants_file (VARIANTS_FILE_FIELD) - "Слова для речень", приходит в extra_files
Без любого из них импорт не выполняется

Импорт возможен только в пустое задание (без шагов)

Порядок импорта - метод .import_file():
-Получает пустое задание и проверяет, что передан файл "Слова для речень"
-Разбирает и проверяет файл предложений
-Разбирает и проверяет файл "Слова для речень"
-Записывает предложения и варианты слов в одной транзакции
-Возвращает список предложений задания

Файл предложений:
-Шапка пропускается до первой строки с латиницей в первой ячейке
-Пустые строки пропускаются, лишние пробелы убираются
-Вариант определяется по файлу - метод ._is_fill():
есть пропуск (__ и больше подчёркиваний) хотя бы в одной строке - "Доповнити речення",
иначе - "Скласти речення"

"Скласти речення" (build) - метод ._parse_build_row():
-Столбцы: речення англійською, переклад, (третий - игнорируется)
-Больше 3 заполненных столбцов, пропуск ___ или меньше 2 слов - ошибка
-Предложение разбивается на токены (слова и знаки препинания)
-Первое слово всегда с заглавной,
а флаг is_lowercase первого токена выставляется по эвристике - метод ._set_lowercase_flags():
    -формы I и слова, которые встречаются с заглавной внутри предложений - с заглавной
    -служебные слова (SERVICE_WORDS) и слова, которые встречаются со строчной - со строчной

"Доповнити речення" (fill) - метод ._parse_fill_row():
-Столбцы: речення з пропусками, слово 1-3 (ответы для пропусков), переклад
-Больше 5 заполненных столбцов - ошибка
-Пропуски любой длины заменяются на ___ (GAP_MARKER)
-Количество пропусков должно совпадать с количеством ответов
-"-" в ответе - нулевой артикль (ZERO_ARTICLE), в собранном предложении на его месте ничего нет
-Полное предложение собирается из шаблона и ответов - метод ._fill_gaps()
-Токены предложения - только ответы для пропусков

Для обоих вариантов:
-Токен длиннее MAX_TOKEN_LENGTH (50 символов) - ошибка
-Ошибка в строке содержит её номер в файле - метод ._row_error()
(для формы в модалке, без номера строки)

Запись в БД (в одной транзакции, после проверки обоих файлов):
-по шагу на каждое предложение - метод ._create_steps():
EnglishTaskStep, Sentence и SentenceToken (._create_sentence_tokens())
-группы вариантов слов - SentenceWordVariant (из SentenceWordVariantMixin)

Возвращает - метод ._get_sentences_list() (из SentenceMixin):
{"sentences": [{"step_id", "answer", "prompt", "template", "gaps", "zero_gaps", "parts"}],
"is_fill", "required_correct_answers"}

Из ошибок, могут подниматься:
-NotFoundError - задание не найдено
-ConflictError - в задании уже есть шаги
-ValidationError - нет одного из файлов, ошибка чтения файла,
ошибка в строке предложений (с номером строки),
ошибка в строке "Слова для речень" (с названием файла и номером строки)
"""

import csv
import re

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from english.models.sentence import Sentence
from english.models.english_task import EnglishTask
from english.models.sentence_token import SentenceToken
from english.services.exceptions import ValidationError
from english.services.task_importers.base import BaseEnglishTaskImporter
from english.services.sentence_text import (
    normalize_spaces, normalize_sentence, 
    tokenize, join_tokens
)
from english.services.task_importers.mixins import SentenceMixin, SentenceWordVariantMixin


class SentenceImporter(
        BaseEnglishTaskImporter,
        SentenceMixin,
        SentenceWordVariantMixin
    ):
    
    # Токеном является любая часть предложения, будь-то слово или знак (. , ; : и пр.)
    # Максимальная длина токена установлена базой (БД) в 50 символов. 
    # Сервер при импорте следует этому ограничению
    MAX_TOKEN_LENGTH = 50
    
    # Подсказала нейрона
    # По паттерну литер латинского алфавита определяется то, 
    # начались ли предложения, которые необходимо обрабатывать и записывать в БД, 
    # или первые строки csv заняты заголовками, такими как "Переклад", "Речення", "Слово 1" и т. д.
    # Короче говоря: те строки, значения с которых должны быть записаны в БД, 
    # всегда имеют в себе латинские буквы, на то и будет идти проверка
    LATIN_PATTERN = re.compile(r"[A-Za-z]")
    # Паттерн пропусков, обозначенных разным количеством нижних подчеркиваний (_)
    # Используется в варианта задания "Доповнити речення"
    GAP_PATTERN = re.compile(r"_{2,}")
    
    # Формы I
    # Как известно, I пишется с большой буквы во всех своих формах, будь-то I или I'll
    # Я решил вынести это в отдельный набор форм I
    # обрабтите внимание что это именно тип set
    I_FORMS = {"i", "i'm", "i'll", "i've", "i'd"}
    
    SERVICE_WORDS = {
        "a", "an", "the",
        "he", "she", "it", "we", "they", "you",
        "my", "his", "her", "its", "our", "their", "your",
        "this", "that", "these", "those", "there",
        "what", "where", "when", "why", "how", "who",
    }
    
    GAP_MARKER = "___"
    # Нулевой артикль, которым обозначен основной вариант вставки, 
    # или один из вариантов вставки в варианте задания "Доповнити речення"
    ZERO_ARTICLE = "-"
    
    # Вырезка колонок со словами, которыми будут заполняться пропуски
    # В актуальной версии таблиц это колонки с 1 по 3 включительно
    FILL_ANSWER_COLUMNS = slice(1, 4)
    
    # Полное украинское предложение, которое у студента будет отображено как вопрос
    FILL_PROMPT_COLUMN = 4
    
    
    # Ограничения для парсинга варианта задания "Предложения"
    # С ними невозможно загрузить csv для других вариантов заданий, 
    # например, варианта задания "Слова"
    BUILD_MAX_COLUMNS = 3
    FILL_MAX_COLUMNS = 5
    MIN_SENTENCE_WORDS = 2
    
    def import_file(
            self, 
            task_id: int,
            file: UploadedFile,
            extra_files: dict | None = None # доп файлы, например "Слова для речень"
        ) -> dict:
        
        task = self._get_empty_task(task_id=task_id)
        word_variants_file = self._get_variants_file(extra_files=extra_files)
        
        rows = self._skip_header(
            rows=self._read_rows(file=file)
        )
        
        if not rows:
            raise ValidationError(
                "У файлі немає жодного речення"
            )
        
        # С этого момента, в наименовании используются слова fill и build:
        # build - вариант задания "Речення" (єто сборка предложения с нуля)
        # fill - вариант задания "Доповнити речення" 
        if self._is_fill(rows=rows):
            sentences = self._parse_fill_rows(rows=rows)
        else:
            sentences = self._parse_build_rows(rows=rows)
        
        # Группировка вариантов слов происходит по рядку,
        # то есть один рядок csv - одна группа вариантов слов
        word_variants_groups = self._parse_variants_file(
            file=word_variants_file
        )
        
        with transaction.atomic():
            self._create_steps(
                task=task,
                sentences=sentences
            )
            
            self._create_word_variants(
                task=task,
                groups=word_variants_groups
            )
        
        return self._get_sentences_list(task=task)
    
    def _skip_header(
            self, 
            rows: list[tuple[int, list[str]]]
        ) -> list[tuple[int, list[str]]]:
        
        for index, (line, cells) in enumerate(rows):
            if self.LATIN_PATTERN.search(cells[0]):
                return rows[index:]
        
        return []
    
    def _read_rows(
            self, 
            file: UploadedFile
        ) -> list[tuple[int, list[str]]]:
        
        reader = csv.reader(
            self._read_text(file=file)
        )
        rows = []
        
        try:
            for cells in reader:
                cleaned = [
                    normalize_spaces(cell) for cell in cells
                ]
                
                # если после очистки строк от лшних пробелов єти строки вообще остались
                if any(cleaned):
                    rows.append(
                        (reader.line_num, cleaned)
                    )
                
        except csv.Error as error:
            raise ValidationError(
                f"Рядок {reader.line_num}: пошкоджений csv"
            ) from error
        
        return rows
    
    def _is_fill(self, rows: list[tuple[int, list[str]]]) -> bool:
        
        for line, cells in rows:
            if self.GAP_PATTERN.search(cells[0]):
                return True
        
        return False

    # rows а не row
    # не путайте
    def _parse_fill_rows(
            self, 
            rows: list[tuple[int, list[str]]]
        ) -> list[dict]:
        
        sentences = []
        
        for line, cells in rows:
            sentences.append(
                self._parse_fill_row(line=line, cells=cells)
            )
        
        return sentences
    
    # row а не rows
    # не путайте
    def _parse_fill_row(
        self,
        line: int,
        cells: list[str]
    ) -> dict:
        
        # Шаблон c пропусками, которые должен будет заполнить студент
        template = self.GAP_PATTERN.sub(
            self.GAP_MARKER, 
            normalize_sentence(cells[0])
        )
        
        answers = [
            normalize_sentence(cell) for cell in cells[self.FILL_ANSWER_COLUMNS] if cell
        ]
        
        # Украинское предложение
        prompt = cells[self.FILL_PROMPT_COLUMN] if len(cells) > self.FILL_PROMPT_COLUMN else ""
        
        if not self.LATIN_PATTERN.search(template):
            raise ValidationError(
                f"Рядок {line}: немає речення англійською"
            )
        
        if not prompt:
            raise ValidationError(
                f"Рядок {line}: немає речення українською (перекладу)"
            )
        
        if any(cells[self.FILL_MAX_COLUMNS:]):
            raise ValidationError(
                f"Рядок {line}: кількість стовпців перевищує максимальну у завданні типу 'Речення'"
            )
        
        gaps_count = template.count(self.GAP_MARKER)
        
        if gaps_count == 0:
            raise ValidationError(
                f"Рядок {line}: немає пропуску ___"
            )
        
        if gaps_count != len(answers):
            raise ValidationError(
                f"Рядок {line}: пропусків {gaps_count}, а відповідей {len(answers)}"
            )
        
        self._validate_tokens(
            line=line,
            tokens=answers
        )
        
        return {
            "prompt": prompt,
            "template": template,
            "answer": self._fill_gaps(template=template, answers=answers),
            "tokens": answers,
            "first_lowercase": False
        }
    
    def _fill_gaps(
        self,
        template: str,
        answers: list[str]
    ) -> str:
        
        parts = template.split(self.GAP_MARKER)
        filled = parts[0]
        
        # Пересобираем предложение перед записью и возвращением на клиент
        # заполняя, при этом, пропуски
        for answer, part in zip(answers, parts[1:]):
            if answer != self.ZERO_ARTICLE:
                filled += answer
            
            filled += part
        
        sentence = join_tokens(tokenize(filled))
        
        return sentence[:1].upper() + sentence[1:]
    
    # rows а не row
    # не путайте
    def _parse_build_rows(
            self, 
            rows: list[tuple[int, list[str]]]
        ) -> list[dict]:
        
        sentences = []
        
        for line, cells in rows:
            sentences.append(
                self._parse_build_row(
                    line=line,
                    cells=cells
                )
            )
        
        self._set_lowercase_flags(sentences=sentences)
        
        return sentences
    
    # row а не rows
    # не путайте
    def _parse_build_row(
            self, 
            line: int, 
            cells: list[str]
        ) -> dict:
        
        sentence = normalize_sentence(cells[0])
        prompt = cells[1] if len(cells) > 1 else ""
        
        if not self.LATIN_PATTERN.search(sentence):
            raise self._row_error(
                line, message="немає речення англійською"
            )
        
        if not prompt:
            raise self._row_error(
                line, message="немає речення українською (перекладу)"
            )
        
        if any(cells[self.BUILD_MAX_COLUMNS:]):
            raise self._row_error(
                line, message="кількість стовпців перевищує максимальну у завданні типу 'Речення'"
            )
        
        if self.GAP_PATTERN.search(sentence):
            raise self._row_error(
                line, message="у реченні для побудови не може бути пропуску ___"
            )
        
        # Токенизация - разбор предложения на токені
        # Таким образомм мі пересобираем предложение из csv, в едином и фиксированном формате сервера
        # для избежания ошибок с разніми форматами и исключить человеческий фактор при заполнеии основніх таблиц, 
        # которіе загружаются сюда, в приложения
        tokens = tokenize(sentence)
        # Сервер выставляет верхний регистр на первого слова вне зависимости от ситуации (это "Скласти" или "Доповонити")
        tokens[0] = tokens[0][:1].upper() + tokens[0][1:]
        
        words_count = sum(
            1 for token in tokens if self.LATIN_PATTERN.search(token)
        )
        
        if words_count < self.MIN_SENTENCE_WORDS:
            raise self._row_error(
                line, message=f"речення має містити мінімум {self.MIN_SENTENCE_WORDS} слова"
            )
        
        self._validate_tokens(
            line=line,
            tokens=tokens
        )
        
        return {
            "prompt": prompt,
            "answer": join_tokens(tokens),
            "template": "",
            "tokens": tokens,
            "first_lowercase": False,
        }
        
    
    def _set_lowercase_flags(self, sentences: list[dict]):
        
        capital_inside = set()
        lowercase_anywhere = set()
        
        for sentence in sentences:
            for index,token in enumerate(sentence["tokens"]):
                if token.islower():
                    lowercase_anywhere.add(token)
                elif index > 0 and token[:1].isupper():
                    capital_inside.add(token.lower())
        
        for sentence in sentences:
            sentence["first_lowercase"] = self._is_first_lowercase(
                key=sentence["tokens"][0].lower(),
                capital_inside=capital_inside,
                lowercase_anywhere=lowercase_anywhere
            )
    
    def _is_first_lowercase(
            self, 
            key: str, 
            capital_inside: set, 
            lowercase_anywhere: set
        ) -> bool:
        
        if key in self.I_FORMS or key in capital_inside:
            return False
        
        return key in self.SERVICE_WORDS or key in lowercase_anywhere
    
    def _validate_tokens(self, line: int, tokens: list[str]):
        
        for token in tokens:
            if len(token) > self.MAX_TOKEN_LENGTH:
                raise self._row_error(
                    line, message=f"занадто довге слово «{token[:20]}…»"
                )
    
    # прежний _create_steps разбит на: _create_steps, _create_sentence_step, _create_sentence_tokens
    # разбит на части потому, что эти части используются в SentenceStepService
    def _create_steps(
        self,
        task: EnglishTask,
        sentences: list[dict]
    ):
        
        for order, data in enumerate(sentences):
            self._create_sentence_step(
                task=task,
                order=order,
                data=data
            )
    
    def _row_error(
        self, 
        line: int| None, 
        message:str
    ) -> ValidationError:
        
        if line is None:
            return ValidationError(
                message[:1].upper() + message[1:]
            )
        
        return ValidationError(f"Рядок {line}: {message}")
