"""

"""

from django.conf import settings
from django.db import transaction
from django.db.models import Max

from english.models.english_task import EnglishTask
from english.models.sentence import Sentence
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_importers.sentence import SentenceImporter
from english.services.sentence_text import join_tokens, tokenize


class SentenceStepService(SentenceImporter):
    def __init__(self):
        super().__init__()
        
        
    
    def create(
            self,
            task_id: int, 
            data: dict
        ) -> dict:
        
        task = self._get_sentence_task(task_id=task_id)
        sentences = Sentence.objects.filter(step__task=task)
        
        if not sentences.exists():
            raise ValidationError(
                'Спочатку завантажте список речень'
            )
        
        self._validate_variant(
            task_is_fill=sentences.exclude(template="").exists(),
            data=data
        )
        
        parsed = self._parse_form(data=data)
        
        self._set_first_lowercase(
            parsed=parsed,
            other_answers=sentences.values_list(
                "answer", 
                flat=True
            )
        )
        
        # Выбираем следующий order для шага
        max_order = task.steps.aggregate(Max("order"))["order__max"]
        order = 0 if max_order is None else max_order + 1
        
        with transaction.atomic():
            self._create_sentence_step(
                task=task, 
                order=order,
                data=parsed
            )
            
        return self._get_sentences_list(task=task)
        
    def update(
            self,
            task_id: int, 
            data: dict,
            step_id: int
        ) -> dict:
        
        task = self._get_sentence_task(task_id=task_id)
        
        sentence = Sentence.objects.filter(
            step_id=step_id,
            step__task=task
        ).first()
        
        if sentence is None:
            raise NotFoundError(
                "Речення не знайдено в цьому завданні"
            )
        
        self._validate_variant(
            task_is_fill=sentence.is_fill, 
            data=data
        )
        
        parsed = self._parse_form(data=data)
        
        self._set_first_lowercase(
            parsed=parsed,
            other_answers=Sentence.objects.filter(
                step__task=task
            ).exclude(pk=sentence.pk).values_list("answer", flat=True)
        )
        
        with transaction.atomic():
            sentence.prompt = parsed["prompt"]
            sentence.answer = parsed["answer"]
            sentence.template = parsed["template"]
            sentence.save()
            
            # В случае редактирования предложения отдельным действием удаляем старые токены, 
            # завязанные на него, и пересоздаем новые
            sentence.tokens.all().delete()
            self._create_sentence_tokens(sentence=sentence, data=parsed)
            
        return self._get_sentences_list(task=task)
    
    def _get_sentence_task(self, task_id: int) -> EnglishTask:
        
        task = EnglishTask.objects.filter(
            id=task_id,
            type="sentences",
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError(
                "Завдання не знайдено"
            )
        
        return task
    
    # variant - вариант предложения: "Скласти речення", "Доповнити речення"
    def _validate_variant(self, task_is_fill: bool, data: dict):
        
        is_fill = False
        
        if "gaps" in data.keys():
            is_fill = True
        
        if is_fill != task_is_fill:
            raise ValidationError(
                "Тип речення не збігається з іншими реченнями завдання"
            )
    
    def _parse_form(self, data: dict) -> dict:
        
        # _prase_build_row унаследован из SentenceImporter
        parsed =  self._parse_build_row(
            line=None,
            cells=[
                str(data.get("answer", "")),
                str(data.get("prompt", ""))
            ]
        )
        
        if "gaps" not in data:
            return parsed
        
        gaps = self._parse_gaps(
            gaps=data["gaps"],
            tokens=parsed["tokens"]
        )
        zero_gaps = self._parse_zero_gaps(
            zero_gaps=data.get("zero_gaps", []),
            tokens=parsed["tokens"]
        )
        
        if not gaps and not zero_gaps:
            raise ValidationError("Відсутні пропуски")
        
        # токены предложения для поля template этого предложения (его записи если быть точнее)
        template_tokens = []
        # токены из которых состоит предложение и котороые будут отображены на странице
        answers = []
        
        for index in range(len(parsed["tokens"]) + 1):
            if index in zero_gaps:
                template_tokens.append(self.GAP_MARKER)
                answers.append(self.ZERO_ARTICLE)
            
            if index == len(parsed["tokens"]):
                break
            
            if index in gaps:
                template_tokens.append(self.GAP_MARKER)
                answers.append(parsed["tokens"][index])
            else:
                template_tokens.append(parsed["tokens"][index])
        
        parsed["template"] = join_tokens(template_tokens)
        parsed["tokens"] = answers
        parsed["first_word_gap"] = 0 in gaps and 0 not in zero_gaps
        
        return parsed
    
    def _parse_zero_gaps(self, zero_gaps, tokens: list[str]) -> list[int]:
        
        if not isinstance(zero_gaps, list):
            raise ValidationError(
                "Некоректні нульові артиклі"
            )
        
        # После убора пропусков, длина zero_gaps оригинального и zero_gaps без пропусков не могут не совпадать
        # если не совпадают - значит при сборке тела запроса были допущены ошибки
        if len(set(zero_gaps)) != len(zero_gaps):
            raise ValidationError(
                "Нульові артиклі не можуть повторюватися"
            )
        
        for zero_gap in zero_gaps:
            # второе <= ибо нулевой артикль может стоять после последнего слова
            if type(zero_gap) != int or not 0 <= zero_gap <= len(tokens):
                raise ValidationError(
                    "Некоректна позиція нульового артикля"
                )
        
        return sorted(zero_gaps)
    
    def _parse_gaps(self, gaps, tokens: list[str]) -> list[int]:
        
        if not isinstance(gaps, list):
            raise ValidationError(
                "Позначте коректно пропуски"
            )
        
        # После убора пропусков, длина gaps оригинального и gaps без пропусков не могут не совпадать
        # если не совпадают - значит при сборке тела запроса были допущены ошибки
        if len(set(gaps)) != len(gaps):
            raise ValidationError(
                "Пропуски не можуть повторюватися"
            )
        
        for gap in gaps:
            if type(gap) != int or not 0 <= gap < len(tokens):
                raise ValidationError(
                    "Некоректний номер пропуску"
                )
            
            if not any(char.isalnum() for char in tokens[gap]):
                raise ValidationError(
                    "Розділові знаки не можуть бути пропусками"
                )
        
        return sorted(gaps)
    
    def _set_first_lowercase(
            self, 
            parsed: dict, 
            other_answers
        ):
        
        current = {
            "tokens": tokenize(parsed["answer"])
        }
        others = [
            {
                "tokens": tokenize(answer)
            } for answer in other_answers
        ]
        
        self._set_lowercase_flags(sentences=others + [current])
        
        # если шаблон предложения есть и НЕ начинается с пропуска, то сервер выставляет для него заглавную букву
        if parsed["template"] and not parsed.get("first_word_gap"):
            parsed["first_lowercase"] = False
        else:
            parsed["first_lowercase"] = current["first_lowercase"]
    
    def sentence_preview(self, task_id: int, data: dict) -> dict:
        
        task = self._get_sentence_task(
            task_id=task_id)
        
        if not Sentence.objects.filter(
            step__task=task
        ).exclude(template="").exists():
            raise ValidationError(
                "Завдання не містить речень з пропусками"
            )
        
        parsed_form = self._parse_form(data=data)
        
        return {
            "tokens": [
                {
                    "index": index,
                    "text": text,
                    # isalnum() определяет, состоит ли строка из букв или цифр
                    # необходимо для того, чтобы не пропускать разделительные знаки на клиент, 
                    # для выбора пропусков. Потому что разделительные знаки нельзя поставить в качестве пропуска
                    "is_word": any(char.isalnum() for char in text)
                }
                for index, text in enumerate(parsed_form["tokens"])
            ]
        }
