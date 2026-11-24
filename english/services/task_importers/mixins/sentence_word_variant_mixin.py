"""
Миксин SentenceImporter: файл "Слова для речень" задания типа "Речення"

Подключается в SentenceImporter, вызывается из .import_file()

Что делает:
-Получает файл из дополнительных файлов запроса - метод ._get_variants_file()
-Разбирает и проверяет файл - метод ._parse_variants_file()
-Записывает группы вариантов слов в БД - метод ._create_word_variants()

Разбор файла:
-Чтение строк - через ._read_rows() импортёра (пустые строки пропускаются)
-Шапка пропускается до первой строки без кириллицы - метод ._skip_variants_header()
-Одна строка - одна группа вариантов слов (например: carry, carried, carries)
-Разбор строки - метод ._parse_variants_row():
    -пустые ячейки пропускаются
    -каждая ячейка - одно слово или "-" (нулевой артикль) - метод ._validate_variant_word()
    -слово не длиннее MAX_TOKEN_LENGTH
    -повторы слова в строке (без учёта регистра) убираются
    -в группе минимум MIN_VARIANT_GROUP_SIZE разных слова

Строки файла не связаны с предложениями по номеру,
варианты подбираются по токенам предложения при прохождении

Запись в БД - SentenceWordVariant:
-row - номер группы, position - номер слова в группе
-text - слово как в файле, normalized - в нижнем регистре (для поиска)
-старые варианты задания перед записью удаляются
Вызывается внутри транзакции импорта

Берёт у класса, в который подключён:
-константы VARIANTS_FILE_FIELD, VARIANTS_FILE_LABEL, CYRILLIC_PATTERN,
MIN_VARIANT_GROUP_SIZE, ZERO_ARTICLE, MAX_TOKEN_LENGTH
-метод ._read_rows()

Из ошибок, может подниматься ValidationError:
-файл "Слова для речень" не передан или в нём нет строк со словами
-ошибка в строке (с названием файла и номером строки)
"""

import re

from django.core.files.uploadedfile import UploadedFile

from english.models.english_task import EnglishTask
from english.models.sentence_word_variant import SentenceWordVariant
from english.services.exceptions import ValidationError
from english.services.sentence_text import normalize_sentence, tokenize
from english.services.task_importers.mixins.base import SentenceMixinBase


class SentenceWordVariantMixin(SentenceMixinBase):
    
    VARIANTS_FILE_FIELD = "variants_file"
    VARIANTS_FILE_LABEL = "Слова для речень"
    CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ]")
    # Минимальное количество вариантов слов в группе вариантов слов
    MIN_VARIANT_GROUP_SIZE = 2
    
    def _get_variants_file(self, extra_files: dict | None) -> UploadedFile:
        
        if not extra_files:
            extra_files = {}
        
        variants_file = extra_files.get(self.VARIANTS_FILE_FIELD)
        
        if variants_file is None:
            raise ValidationError(
                f"Завантажте файл «{self.VARIANTS_FILE_LABEL}»"
            )
        
        return variants_file
    
    def _parse_variants_file(self, file: UploadedFile) -> list[list[str]]:
            
        rows = self._skip_variants_header(
            rows=self._read_rows(file=file)
        )
        
        if not rows:
            raise ValidationError(
                f"У файлі «{self.VARIANTS_FILE_LABEL}» немає жодного рядка зі словами"
            )
        
        return [
            self._parse_variants_row(line=line, cells=cells)
            for line, cells in rows
        ]
    
    def _skip_variants_header(
            self, 
            rows: list[tuple[int, list[str]]]
        ) -> list[tuple[int, list[str]]]:
        
        for index, (line, cells) in enumerate(rows):
            if not any(
                self.CYRILLIC_PATTERN.search(cell) for cell in cells
                ):
                return rows[index:]
        
        return []
    
    def _parse_variants_row(
            self, 
            line: int, 
            cells: list[str]
        ) -> list[str]:
        
        group = []
        normalized_words = set()
        
        for cell in cells:
            word = normalize_sentence(cell)
            
            if not word:
                continue
            
            self._validate_variant_word(line=line, word=word)
            
            if word.lower() in normalized_words:
                continue
            
            normalized_words.add(word.lower())
            group.append(word)
        
        if len(group) < self.MIN_VARIANT_GROUP_SIZE:
            raise self._variants_row_error(
                line=line,
                message=f"має бути щонайменше {self.MIN_VARIANT_GROUP_SIZE} різних слова"
            )
        
        return group
    
    def _validate_variant_word(self, line: int, word: str):
        
        if word == self.ZERO_ARTICLE:
            return
        
        tokens = tokenize(word)
        
        if len(tokens) != 1 or not tokens[0][0].isalnum():
            raise self._variants_row_error(
                line=line,
                message=f"«{word}» має бути одним словом"
            )
        
        if len(word) > self.MAX_TOKEN_LENGTH:
            raise self._variants_row_error(
                line=line,
                message=f"слово «{word}» довше за {self.MAX_TOKEN_LENGTH} символів"
            )
    
    def _variants_row_error(
            self, 
            line: int, 
            message: str
        ) -> ValidationError:
        
        return ValidationError(
            f"«{self.VARIANTS_FILE_LABEL}», рядок {line}: {message}"
        )
    
    def _create_word_variants(
            self, 
            task: EnglishTask, 
            groups: list[list[str]]
        ):
        
        task.word_variants.all().delete()
        
        SentenceWordVariant.objects.bulk_create([
            SentenceWordVariant(
                task=task,
                row=row,
                position=position,
                text=word,
                normalized=word.lower()
            )
            for row, group in enumerate(groups)
            for position, word in enumerate(group)
        ])
