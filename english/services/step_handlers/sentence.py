"""

"""

import random

from english.models.sentence import Sentence
from english.models.sentence_token import SentenceToken
from english.models.sentence_word_variant import SentenceWordVariant
from english.services.exceptions import ValidationError
from english.services.sentence_text import join_tokens, tokenize
from english.services.step_handlers.base import StepHandler
from english.models.english_task_step import EnglishTaskStep
from english.models.student_answer import StudentAnswer
from english.services.task_importers.sentence import SentenceImporter


class SentenceHandler(StepHandler):
    
    MAX_VARIANTS_PER_TOKEN = 3
    MAX_VARIANTS = 6
    
    def get_step_data(self, step: EnglishTaskStep) -> dict:
        
        sentence = self._get_sentence(step=step)
        tokens = list(
            sentence.tokens.order_by("order")
        )
        
        if sentence.template:
            return self._get_fill_step_data(
                step=step,
                sentence=sentence,
                tokens=tokens
            )
        
        return self._get_build_step_data(
            step=step,
            sentence=sentence,
            tokens=tokens
        )
    
    def _get_build_step_data(
        self,
        step:EnglishTaskStep,
        sentence: Sentence,
        tokens: list[SentenceToken]
    ) -> dict:
        
        tokens_bank = [
            self._display_token(token=token) for token in tokens
        ]
        tokens_bank += self._get_variants(
            task_id=step.task_id,
            words=[
                token.text for token in tokens if self._is_word(token.text)
            ]
        )
        
        random.shuffle(tokens_bank)
        
        return {
            "id": step.id,
            "kind": step.kind,
            "variant": "build",
            "prompt": sentence.prompt,
            "tokens": tokens_bank # образно называю набор токенов "банкой". 
            # На этом моменте в банке находятся и токены самого предложения (SentenceToken), 
            # и дополнительные варианты (SentenceWordVariant)
        }
    
    def _get_fill_step_data(
        self,
        step: EnglishTaskStep,
        sentence: Sentence,
        tokens: list[SentenceToken]
    ) -> dict:
        
        tokens_bank = [
            self._display_token(token=token) for token in tokens
        ]
        
        tokens_bank += self._get_task_answer_variants(
            step=step,
            sentence=sentence,
            answers=[token.text for token in tokens]
        )
        
        random.shuffle(tokens_bank)
        
        return {
            "id": step.id,
            "kind": step.kind,
            "variant": "fill",
            "prompt": sentence.prompt,
            "template": self._split_template(
                template=sentence.template
            ),
            "tokens": tokens_bank
        }
    
    def _get_task_answer_variants(
        self,
        step: EnglishTaskStep,
        sentence: Sentence,
        answers: list[str]
    ) -> list[str]:
        normalized_answers = {
            answer.lower() for answer in answers
        }
        candidates = {}
        
        task_answers = SentenceToken.objects.filter(
            sentence__step__task_id=step.task_id
        ).exclude(
            sentence=sentence
        ).values_list('text', flat=True)
        
        for text in task_answers:
            key = text.lower()
            
            if key in normalized_answers:
                continue
            
            if key not in candidates or text.islower():
                candidates[key] = self._display_variants(text)
        
        count = min(
            len(candidates),
            self.MAX_VARIANTS,
            self.MAX_VARIANTS_PER_TOKEN * len(answers)
        )
        
        return random.sample(
            list(candidates.values()),
            k=count
        )
    
    def _split_template(self, template: str) -> list[str]:
        
        pieces = template.split(SentenceImporter.GAP_MARKER)
        result = []
        
        for index, piece in enumerate(pieces):
            result += tokenize(piece)
            
            if index < len(pieces) -1:
                result.append(SentenceImporter.GAP_MARKER)
        
        return result
    
    def _check_build(self, sentence: Sentence, data: dict) -> bool:
        
        tokens = data.get("tokens")
        
        if not isinstance(tokens, list) or not tokens or not all(isinstance(token, str) for token in tokens):
            raise ValidationError("Некоректна відповідь")
        
        answer = join_tokens(tokens)
        answer = answer[:1].upper() + answer[1:]
        
        return answer == sentence.answer
    
    def _check_fill(self, sentence: Sentence, data:dict) -> bool:
        answers = data.get("answers")
        expected = []
        
        for token in sentence.tokens.order_by('order'):
            expected.append(token.text)
        
        if not isinstance(answers, list) or not all(isinstance(answer, str) for answer in answers):
            raise ValidationError("Некоректна відповідь")
        
        if len(answers) != len(expected) or any(not answer.strip() for answer in answers):
            raise ValidationError("Заповніть усі пропуски")
        return all(
            answer.strip().lower() == correct.lower() for answer, correct in zip(answers, expected)
        )
    
    def check(self, step: EnglishTaskStep, data: dict) -> bool:
        
        sentence = self._get_sentence(step=step)
        
        if sentence.template:
            return self._check_fill(sentence=sentence, data=data)
        
        return self._check_build(sentence=sentence, data=data)
    
    def save_answer_details(
            self, 
            answer: StudentAnswer, 
            step: EnglishTaskStep, 
            data: dict
        ):
        
        pass
    
    def _get_variants(
            self, 
            task_id: int, 
            words: list[str],
            allow_zero: bool = False
        ) -> list[str]:
        
        normalized_words = {word.lower() for word in words}
        
        matches = list(
            SentenceWordVariant.objects.filter(
                task_id=task_id,
                normalized__in=normalized_words
            ).values_list("row", "position", "normalized")
        )
        
        if not matches:
            return []
        
        groups = {}
        
        word_variants_by_position = SentenceWordVariant.objects.filter(
            task_id=task_id,
            row__in={row for row, _, _ in matches}
        ).order_by("row", "position")
            
        
        for variant in word_variants_by_position:
            groups.setdefault(
                variant.row, 
                []
            ).append(variant)
        
        variants = {}
        
        for word in normalized_words:
            rows = [
                row for row, position, normalized in matches if normalized == word and position == 0
            ]
            
            if not rows:
                rows = [
                    row for row, position, normalized in matches
                    if normalized == word
                ]
            
            candidates = {}
            
            for row in rows:
                for variant in groups.get(row, []):
                    
                    if variant.normalized in normalized_words or variant.normalized in variants or (not allow_zero and variant.text == SentenceImporter.ZERO_ARTICLE):
                        continue
                    
                    candidates[variant.normalized] = self._display_variants(variant.text)
        
            if not candidates:
                continue
            
            picked = random.sample(
                list(candidates.items()),
                k=random.randint(1, min(self.MAX_VARIANTS_PER_TOKEN, len(candidates)))
            )

            variants.update(picked)
        
        result = list(variants.values())
        
        if len(result) > self.MAX_VARIANTS:
            result = random.sample(result, k=self.MAX_VARIANTS)
        
        return result
    
    def _display_variants(self, text: str) -> str:
        
        if text.lower() in SentenceImporter.I_FORMS:
            return text[:1].upper() + text[1:].lower()
        
        return text
    
    def _is_word(self, text: str) -> bool:
        return any(char.isalnum() for char in text)
    
    def _display_token(self, token: SentenceToken) -> str:
        
        if token.order == 0 and token.is_lowercase:
            return token.text[:1].lower() + token.text[1:]
        
        return token.text
    
    def _get_sentence(self, step: EnglishTaskStep) -> Sentence:
        
        try:
            return step.sentence
        except Sentence.DoesNotExist as error:
            raise ValidationError(
                "Речення цього кроку відсутнє"
            ) from error
