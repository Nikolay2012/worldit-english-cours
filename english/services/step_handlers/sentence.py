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
        # Получаем токены предложения (его части)
        # Этот этап свойственнен обоим вариантам предложений: "Скласти" (обозначено как build) и "Доповнити" (fill)
        tokens = list(
            sentence.tokens.order_by("order")
        )
        
        # Если в записи предложения (Sentence) указан шаблон (sentence.template)
        # То это поле варианта "Доповнити"
        # Если template не заполнен, то это вариант "Скласти"
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
        
        # Собранный набор токенов предложения "Скласти"
        # На данном этапе присутствуют только те токены, 
        # которые будут непосредственно использованы при сборке
        # Другими словами: неправильным вариантов ещё нету
        tokens_bank = [
            self._display_token(token=token) for token in tokens
        ]
        
        # На этом этапе добавляются альтернативные токены, неправильные
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
        
        answers = {}
        
        for token in tokens:
            # Записываем варианты токенов через setdefault
            # таким образом, будет записано значение только если такого ключа ещё нет
            # Если ключ есть, то ничего не изменится
            # Благодаря этой части, у студента не будут повторяться вставки в заданиях, 
            # где они дублируются в предложении
            # Примером такого задания будет: The Pacific Ocean is one of the five oceans of the world.
            # Здесь вставка артикля the повторяется трижды
            # Без setdefault у студента было бы три токена банке, получилось бы: a, an, the, the, the
            # Очевидно, что нужно вставить три the
            answers.setdefault(
                token.text.lower(), 
                self._display_token(token=token)
            )
        
        # Собранный набор токенов предложения "Доповнити"
        # На данном этапе присутствуют только те токены, 
        # которые будут непосредственно использованы при сборке
        # Другими словами: неправильным вариантов ещё нету
        tokens_bank = list(answers.values())
        
        # На этом этапе добавляются альтернативные токены, неправильные
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
        
        # сведение к нижнему регистру ответов 
        normalized_answers = {
            answer.lower() for answer in answers
        }
        candidates = {}
        
        # Отбираем только текста токенов необходимого предложения (необходимое предложение - переданный sentence)
        task_answers = SentenceToken.objects.filter(
            sentence__step__task_id=step.task_id
        ).exclude(
            sentence=sentence
        ).values_list('text', flat=True)
        
        for text in task_answers:
            key = text.lower()
            
            # Чтобы не прогонять все варианты токенов через нормалиацию (сведение к нижнему регистру)
            if key in normalized_answers:
                continue
            
            # Если вариант токена не указан в кандидатах к отправке на клиент
            # 
            if key not in candidates or text.islower():
                candidates[key] = self._display_variants(text)
        
        # Подбираем количество необходимых для отображения вариантов токенов
        count = min(
            len(candidates),
            self.MAX_VARIANTS,
            self.MAX_VARIANTS_PER_TOKEN * len(answers)
        )
        
        # Отбираем необходимое количество вариантов токенов в случайном порядке
        return random.sample(
            list(candidates.values()),
            k=count
        )
    
    def _split_template(self, template: str) -> list[str]:
        
        pieces = template.split(SentenceImporter.GAP_MARKER)
        result = []
        
        for index, piece in enumerate(pieces):
            # Разбиваем кусок предложения через tokenize (без ___)
            result += tokenize(piece)
            
            # Пока не дойдем до последнего куска предложения, подставляем ___ между частями
            # Таким образом собираем список result с кусками предложения (template-а) для отображения на клиенте:
            # Пкак пример: I __ to school
            # будет: ["I", "___", "to", "school"]
            if index < len(pieces) -1:
                result.append(SentenceImporter.GAP_MARKER)
        
        return result
    
    def _check_build(self, sentence: Sentence, data: dict) -> bool:
        
        # Получаем набор токенов, переданным с клиента
        tokens = data.get("tokens")
        
        # Набор токенов должен бтыь списком, и каждый токен этого списка должен быть строкой
        if not isinstance(tokens, list) or not tokens or not all(isinstance(token, str) for token in tokens):
            raise ValidationError("Некоректна відповідь")
        
        # Собираем токены в предложение - answer
        # Такого формата ответ студента и будет проверен
        answer = join_tokens(tokens)
        
        # Возводим в верхний регистр первый символ предложения
        answer = answer[:1].upper() + answer[1:]
        
        return answer == sentence.answer
    
    def _check_fill(self, sentence: Sentence, data:dict) -> bool:
        answers = data.get("answers")
        expected = []
        
        # Подготавливаем необходимое количество вставок
        for token in sentence.tokens.order_by('order'):
            expected.append(token.text)
        
        # Набор вставок в предложений "Доповнити" (по сути токенов ответа) должен быть списком,
        # и каждый токен (эта же вставка) должна быть строкой
        if not isinstance(answers, list) or not all(isinstance(answer, str) for answer in answers):
            raise ValidationError("Некоректна відповідь")
        
        # Количество вставок студента должно быть равно ожидаемомму количеству вставок
        # Также, очевидно, вставки должны присутствовать, а значит - вставки не могут быть пустыми
        if len(answers) != len(expected) or any(not answer.strip() for answer in answers):
            raise ValidationError("Заповніть усі пропуски")
        
        # Возвращаем правильность ответа если 
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
        
        answer.built_sentence = self._get_built_sentence(
            sentence=self._get_sentence(step=step),
            data=data
        )
        answer.save(update_fields=["built_sentence"])
    
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
        
        # В БД токены записаны в оригинальном виде, они могут быть в верхнем регистре
        # Если передать токены в верхнем регистре на клиент, 
        # это будет очевидной подсказкой для проходящего студента
        # Потому: если order токена = 0, или если в записи токена is_lowercase поставлен на True
        if token.order == 0 and token.is_lowercase:
            # То собираем этот токен заново, сведя регистр первого символа к нулю
            return token.text[:1].lower() + token.text[1:]
        
        return token.text
    
    def _get_sentence(self, step: EnglishTaskStep) -> Sentence:
        
        try:
            return step.sentence
        except Sentence.DoesNotExist as error:
            raise ValidationError(
                "Речення цього кроку відсутнє"
            ) from error
    
    # Метод собирает предложение из токенов, которые составил студент
    # По собранному предложению будет определено его совпадение с исходным предложением,
    # вне зависимости от варианта предложения, будь-то "Скласти" или же "Доповнити"
    # Сравниваются только собранные предложения, а не отдельные токены
    def _get_built_sentence(self, sentence: Sentence, data: dict) -> str:
        
        # Если предложение варинта "Скласти"
        if not sentence.template:
            built = join_tokens(
                data["tokens"]
            )
        
        # Если предложение варианта "Допвонити", т. е. у него записан sentence.template
        else :
            pieces = sentence.template.split(
                SentenceImporter.GAP_MARKER
            )
            
            filled = pieces[0]
            
            for answer, piece in zip(data["answers"], pieces[1:]):
                if answer.strip() != SentenceImporter.ZERO_ARTICLE:
                    filled += answer.strip()
                
                filled += piece
            
            built = join_tokens(tokenize(filled))
            
        return built[:1].upper() + built[1:]
