"""
Сервис создания, редактирования и предпросмотра одного предложения
в задании типа "Речення"

Используется эндпоинтами:
-SentenceEndpoint - создание и редактирование предложения из модалки списка речень
-SentencePreviewEndpoint - разбор предложения на токены для выбора пропусков

Доступ к эндпоинтам - admin

Наследует SentenceImporter, откуда берёт разбор и проверку предложения,
выставление регистра первого слова, создание шага с токенами,
сбор списка предложений для клиента и константы (GAP_MARKER, ZERO_ARTICLE и др.)

Задание ищется только среди заданий курса английского с типом "sentences"

Вариант предложения определяется по данным запроса:
-есть поле gaps - "Доповнити речення"
-нет поля gaps - "Скласти речення"
Вариант должен совпадать с вариантом остальных предложений задания,
смешивать варианты в одном задании нельзя

Создание предложения - метод .create():
-Работает только если в задании уже есть предложения (после импорта csv)
-Проверяет, что вариант совпадает с остальными предложениями задания
-Разбирает предложение - метод ._parse_form()
-Выставляет регистр первого слова с учётом остальных предложений задания
-Создаёт новый шаг в конце задания вместе с Sentence и SentenceToken

Редактирование предложения - метод .update():
-Проверяет, что предложение есть в этом задании
-Проверяет, что вариант не изменился
-Обновляет текст, перевод и шаблон предложения
-Удаляет старые токены и создаёт новые

Разбор предложения - метод ._parse_form():
-Из полей answer (англійською) и prompt (українською) собирает предложение,
по тем же правилам, что и при импорте csv
-Для "Доповнити речення" дополнительно:
    -gaps - номера токенов, которые станут пропусками,
    знаки препинания пропуском быть не могут
    -inserts - вставки по порядку: {"position", "kind", "text"}
        -position - перед каким токеном стоит вставка (от 0 до количества токенов)
        -kind "zero" - нулевой артикль, не больше одного в позиции
        -kind "mark" - знак препинания (INSERT_MARKS), становится частью предложения
    -должен быть хотя бы один пропуск или нулевой артикль
    -собирает шаблон с ___, полное предложение (со вставленными знаками)
    и список ответов для пропусков (токены SentenceToken)

Регистр первого слова - метод ._set_first_lowercase():
-"Скласти речення" - по той же эвристике, что и при импорте
-"Доповнити речення" - первое слово с заглавной,
если только оно само не является пропуском

Предпросмотр - метод .sentence_preview():
-Только для задания с вариантом "Доповнити речення"
-Возвращает токены предложения с номером и признаком is_word,
чтобы на клиенте нельзя было выбрать знак препинания пропуском

Варианты слов для речень (SentenceWordVariant) этот сервис не меняет:
они привязаны к заданию и подбираются по токенам предложения при прохождении

.create() и .update() возвращают полный список предложений задания

Из ошибок, могут подниматься:
-NotFoundError - задание или предложение не найдено
-ValidationError - пустое предложение или перевод, предложение слишком короткое,
вариант не совпадает с остальными предложениями задания,
некорректные пропуски или нулевые артикли,
в задании ещё нет предложений (при создании) или нет предложений с пропусками (при предпросмотре)
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
        
        self.SENTENCE_INSERT_MARKS = ["-", ",", ".", ":", ";"]
    
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
        
        tokens = parsed["tokens"]
        
        gaps = self._parse_gaps(
            gaps=data["gaps"],
            tokens=tokens
        )
        inserts = self._parse_inserts(
            inserts=data.get("inserts", []),
            tokens=tokens
        )
        
        if not gaps and not any(insert["kind"] == "zero" for insert in inserts):
            raise ValidationError("Відсутні пропуски")
        
        inserts_by_position = {}
        
        for insert in inserts:
            inserts_by_position.setdefault(
                insert["position"],
                []
            ).append(insert)
        
        # токены предложения для поля template этого предложения (его записи если быть точнее)
        template_tokens = []
        # токены из которых состоит предложение и котороые будут отображены на странице
        answers = []
        sentence_tokens = []
        first_word_gap = None
        
        for position in range(len(tokens) + 1):
            for insert in inserts_by_position.get(position, []):
                if insert["kind"] == "zero":
                    template_tokens.append(self.GAP_MARKER)
                    answers.append(self.ZERO_ARTICLE)
                    continue
                
                template_tokens.append(insert["text"])
                sentence_tokens.append(insert["text"])
                
                if first_word_gap is None:
                    first_word_gap = False
            
            if position == len(tokens):
                break
            
            token = tokens[position]
            sentence_tokens.append(token)
            
            if position in gaps:
                template_tokens.append(self.GAP_MARKER)
                answers.append(token)
            else:
                template_tokens.append(token)
            
            if first_word_gap is None:
                first_word_gap = position in gaps
            
            # if index in zero_gaps:
            #     template_tokens.append(self.GAP_MARKER)
            #     answers.append(self.ZERO_ARTICLE)
            
            # if index == len(tokens):
            #     break
            
            # if index in gaps:
            #     template_tokens.append(self.GAP_MARKER)
            #     answers.append(tokens[index])
            # else:
            #     template_tokens.append(tokens[index])
        
        parsed["answer"] = join_tokens(sentence_tokens)
        parsed["template"] = join_tokens(template_tokens)
        parsed["tokens"] = answers
        parsed["first_word_gap"] = bool(first_word_gap)
        
        return parsed
    
    def _parse_inserts(self, inserts, tokens: list[str]) -> list[int]:
        
        if not isinstance(inserts, list):
            raise ValidationError(
                "Некоректні вставки"
            )
        
        parsed = []
        zero_positions = set()
        previous_position = 0
        
        for insert in inserts:
            
            if not isinstance(insert, dict):
                raise ValidationError(
                    "Некоректні вставки"
                )
            
            position = insert.get("position")
            kind = insert.get("kind")
            
            # второе <= ибо нулевой артикль может стоять после последнего слова
            if type(position) != int or not 0 <= position <= len(tokens):
                raise ValidationError(
                    "Некоректна позиція вставки"
                )
            
            if position < previous_position:
                return ValidationError(
                    "Вставки мають йти по порядку"
                )
            
            previous_position = position
            
            if kind == "zero":
                if position in zero_positions:
                    raise ValidationError(
                        "Нульові артиклі не можуть повторюватися"
                    )
                
                zero_positions.add(position)
                parsed.append({
                    "position": position,
                    "kind": "zero"
                })
            elif kind == "mark":
                text = insert.get("text")
                
                if text not in self.SENTENCE_INSERT_MARKS:
                    raise ValidationError("Некоректний розділовий знак")
                
                parsed.append({
                    "position": position,
                    "kind": "mark",
                    "text": text
                })
            else:
                raise ValidationError(
                    "Некоректний тип вставки"
                )
        
        return parsed
    
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
