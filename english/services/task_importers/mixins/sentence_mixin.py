"""
Миксин SentenceImporter: создание шага с предложением и список предложений для клиента

Подключается в SentenceImporter
Через него же доступен в SentenceStepService (создание и редактирование предложения)
Данные одного предложения (._serialize_sentence()) использует также
SentenceHandler.get_list_item() - боковая панель «Список речень» / «Історія відповідей»
Заглушки методов и констант, которые миксин берёт у импортёра, - в SentenceMixinBase

Создание шага - метод ._create_sentence_step():
-EnglishTaskStep с видом "sentence" и порядком order
-Sentence: перевод (prompt), полное предложение (answer), шаблон с пропусками (template)
-SentenceToken - метод ._create_sentence_tokens():
    -"Скласти речення" - все токены предложения
    -"Доповнити речення" - только ответы для пропусков
    -is_lowercase - только у первого токена, по флагу first_lowercase
Вызывается внутри транзакции того, кто создаёт шаг

Список предложений - метод ._get_sentences_list():
-Шаги задания по порядку, токены каждого предложения по order
-Возвращает {"sentences": [...], "is_fill", "required_correct_answers"}
-is_fill - есть ли в задании предложения варианта "Доповнити речення"
-required_correct_answers - сколько правильных ответов нужно на предложение,
из EnglishProgressService (для точек прогресса в списке)

Данные одного предложения - метод ._serialize_sentence():
-step_id, answer, prompt, template
-gaps и zero_gaps - позиции пропусков и нулевых артиклей
в токенах полного предложения - метод ._get_gap_positions()
(нужны модалке редактирования, чтобы снова отметить пропуски;
клиент превращает zero_gaps во вставки kind "zero")
-токены предложения должны быть заранее подгружены по order (Prefetch),
иначе на каждое предложение уйдёт отдельный запрос
-parts - куски предложения для отображения в списке - метод ._get_sentence_parts():
    -{"kind": "text", "text"} - обычный текст
    -{"kind": "gap", "text"} - слово-пропуск (в списке подчёркивается)
    -{"kind": "zero"} - нулевой артикль (в списке ___)
    -у "Скласти речення" - один кусок text с полным предложением
    -первая буква первого видимого куска - заглавная - метод ._capitalize_first_part()

Берёт у класса, в который подключён:
-константы GAP_MARKER, ZERO_ARTICLE
"""

from django.db.models import Prefetch

from english.models.sentence import Sentence
from english.models.english_task_step import EnglishTaskStep
from english.models.sentence_token import SentenceToken
from english.services.progress import EnglishProgressService
from english.services.sentence_text import tokenize
from english.models.english_task import EnglishTask
from english.services.task_importers.mixins.base import SentenceMixinBase


class SentenceMixin(SentenceMixinBase):
    
    def _get_sentences_list(self, task: EnglishTask) -> dict:
        
        steps = task.steps.select_related(
                "sentence"
            ).prefetch_related(
                Prefetch(
                    "sentence__tokens", 
                    queryset=SentenceToken.objects.order_by('order')
                )
            ).order_by('order')
        
        return {
            "sentences": [
                self._serialize_sentence(sentence=step.sentence, step_id=step.id) for step in steps
            ],
            "is_fill": any(step.sentence.is_fill for step in steps),
            "required_correct_answers": EnglishProgressService.get_required_correct_answers("sentences"),
        }
    
    def _serialize_sentence(
        self, 
        sentence: Sentence, 
        step_id: int
    ) -> dict:
        
        answers = [token.text for token in sentence.tokens.all()]
        
        gaps, zero_gaps = self._get_gap_positions(
            template=sentence.template,
            answers=answers
        )
        
        return {
            "step_id": step_id,
            "answer": sentence.answer,
            "prompt": sentence.prompt,
            "template": sentence.template,
            "gaps": gaps,
            "zero_gaps": zero_gaps,
            "parts": self._get_sentence_parts(
                sentence=sentence,
                answers=answers
            )
        }
    
    def _get_sentence_parts(
        self, 
        sentence: Sentence, 
        answers: list[str]
    ) -> list[dict]:
        
        if not sentence.template:
            return [{"kind": "text", "text": sentence.answer}]
        
        pieces = sentence.template.split(self.GAP_MARKER)
        parts = []
        
        for index, piece in enumerate(pieces):
            if piece:
                parts.append({"kind": "text", "text": piece})
            
            if index == len(pieces) - 1:
                break
            
            answer = answers[index] if index < len(answers) else ""
            
            if answer == self.ZERO_ARTICLE:
                parts.append({"kind": "zero"})
            else:
                parts.append({"kind": "gap", "text": answer})
        
        self._capitalize_first_part(parts=parts)
        
        return parts
    
    def _create_sentence_step(
            self,
            task: EnglishTask,
            order: int,
            data: dict
        ):
        
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
        
        self._create_sentence_tokens(
            sentence=sentence,
            data=data
        )
    
    def _capitalize_first_part(self, parts: list[dict]):
        
        for part in parts:
            if part["kind"] == "zero":
                continue
            
            text = part["text"]
            stripped = text.lstrip()
            offset = len(text) - len(stripped)
            
            part["text"] = text[:offset] + stripped[:1].upper() + stripped[1:]
            
            return
    
    def _get_gap_positions(
            self, 
            template: str, 
            answers: list[str]
        ) -> tuple[list[int], list[int]]:
        
        if not template:
            return ([], [])
        
        gaps = []
        zero_gaps = []
        index = 0
        
        # перебираем до последнего элемента
        # например: ['he ', ' she ', ' it']
        # после ' it' ничего нету. Если не делать срез списка, 
        # то будет отмечен пропуск после ' it', что будет ошибкой
        for part, answer in zip(template.split(self.GAP_MARKER)[:-1], answers):
            # подсчитываем, сколько тоенов стоит в куске перед пропусков, 
            # чтобы сдвинуть счетчик
            index += len(tokenize(part))
            
            if answer == self.ZERO_ARTICLE:
                zero_gaps.append(index)
            else:
                gaps.append(index)
                index += 1
        
        return (gaps, zero_gaps)
    
    def _create_sentence_tokens(
            self, 
            sentence: Sentence, 
            data: dict
        ):
        
        SentenceToken.objects.bulk_create([
            SentenceToken(
                sentence=sentence,
                text=text,
                order=index,
                is_lowercase=index == 0 and data["first_lowercase"]
            ) for index, text in enumerate(data["tokens"])
        ])
