"""

"""

import csv
import re

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from english.models.sentence import Sentence
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.models.sentence_token import SentenceToken
from english.services.exceptions import ValidationError
from english.services.task_importers.base import BaseEnglishTaskImporter
from english.services.sentence_text import (
    normalize_spaces, normalize_sentence, 
    tokenize, join_tokens
)


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
    I_FORMS = {"i", "i'm", "i'll", "i've", "i'd"}
    
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
        
        # С этого момента, в наименовании используются слова fill и build:
        # build - вариант задания "Речення" (єто сборка предложения с нуля)
        # fill - вариант задания "Доповнити речення" 
        if self._is_fill(rows=rows):
            sentences = self._parse_fill_rows(rows=rows)
        else:
            sentences = self._parse_build_rows(rows=rows)
        
        with transaction.atomic():
            self._create_steps(
                task=task,
                sentences=sentences
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
        
        raise ValidationError("Імпорт речень з пропусками ще не підтримується")

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
            raise ValidationError(
                f"Рядок {line}: немає речення англійською"
            )
        
        if not prompt:
            raise ValidationError(
                f"Рядок {line}: немає речення українською (перекладу)"
            )
        
        if self.GAP_PATTERN.search(sentence):
            raise ValidationError(
                f"Рядок {line}: у реченні для побудови не може бути пропуску ___"
            )
        
        # Токенизация - разбор предложения на токені
        # Таким образомм мі пересобираем предложение из csv, в едином и фиксированном формате сервера
        # для избежания ошибок с разніми форматами и исключить человеческий фактор при заполнеии основніх таблиц, 
        # которіе загружаются сюда, в приложения
        tokens = tokenize(sentence)
        
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
    
    def _create_steps(
        self,
        task: EnglishTask,
        sentences: list[dict]
    ):
        
        for order, data in enumerate(sentences):
            step = EnglishTaskStep.objects.create(
                task=task,
                order=order,
                kind="sentence"
            )
            
            sentence = Sentence.objects.create(
                step=step,
                prompt=data["prompt"],
                answer=data["answer"],
                template=data["template"]
            )
            
            SentenceToken.objects.bulk_create([
                SentenceToken(
                    sentence=sentence,
                    text=text,
                    order=index,
                    is_lowercase=index == 0 and data["first_lowercase"]
                ) for index, text in enumerate(data["tokens"])
            ])
