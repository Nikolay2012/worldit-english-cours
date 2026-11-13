"""

"""

import csv
import re

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from english.models.english_task import EnglishTask
from english.services.exceptions import ValidationError
from english.services.task_importers.base import BaseEnglishTaskImporter
from english.services.sentence_text import normalize_spaces


class SentenceImporter(BaseEnglishTaskImporter):
    
    REQUIRED_CORRECT_ANSWERS = 6
    
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
    I_FROMS = {"i", "i'm", "i'll", "i've", "i'd"}
    
    SERVICE_WORDS = {
        "a", "an", "the",
        "he", "she", "it", "we", "they", "you",
        "my", "his", "her", "its", "our", "their", "your",
        "this", "that", "these", "those", "there",
        "what", "where", "when", "why", "how", "who",
    }
    
    def import_file(
            self, 
            task_id: int,
            file: UploadedFile
        ) -> dict:
        
        task = self._get_empty_task(task_id=task_id)
        rows = self._skip_header(
            rows=self._read_rows(file=file)
        )
        
        if not rows:
            raise ValidationError(
                "У файлі немає жодного речення"
            )
            
        print(rows)
        
    
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
    
    # row а не rows
    # не путайте
    def _parse_fill_row(
        self,
        line: int,
        cells: list[str]
    ) -> dict:
        
        raise ValidationError("Імпорт речень з пропусками ще не підтримується")
    
    def _validate_tokens(self, line: int, tokens: list[str]):
        
        for token in tokens:
            if len(token) > self.MAX_TOKEN_LENGTH:
                raise ValidationError(f"Рядок {line}: занадто довге слово «{token[:20]}…»")
    
    def _get_sentences_list(self, task: EnglishTask) -> dict:
        
        steps = task.steps.select_related(
            "sentence").order_by('order')
        
        return {
            "sentences": [
                {
                    "step_id": step.id,
                    "answer": step.sentence.answer,
                    "prompt": step.sentence.prompt,
                    "template": step.sentence.template
                } for step in steps
            ],
            "required_correct_answers": self.REQUIRED_CORRECT_ANSWERS
        }
