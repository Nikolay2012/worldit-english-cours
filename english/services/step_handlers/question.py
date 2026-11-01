"""

"""

import random

from english.models.answer_option import AnswerOption
from english.models.english_task_step import EnglishTaskStep
from english.models.question import Question
from english.services.exceptions import ValidationError
from english.services.step_handlers.base import StepHandler


class QuestionHandler(StepHandler):
    
    # Реализуем super().get_step_data() 
    # (слово «реализуем» здесь лишь условное, имитируем интерфейсы)
    def get_step_data(self, step: EnglishTaskStep) -> dict:
        
        question: Question = step.question
        
        answer_options = list(question.options.all())
        # КАк и было решено: сервер перемешивает варианты ответа
        # Для того чтобы исходный порядок нельзя было восстановить на клиенте
        random.shuffle(answer_options)
        
        return {
            "id": step.id,
            "kind": step.kind,
            "prompt": self._get_prompt(question=question),
            "options": [
                {"id": option.id, "text": option.text}
                for option in answer_options
            ]
        }
    
    def check(self, step: EnglishTaskStep, data: dict) -> bool:
        
        try:
            option_id = int(data.get("option_id"))
        except Exception as error:
            raise ValidationError(
                "Некоректний варіант відповіді"
            ) from error
        
        option: AnswerOption = step.question.options.filter(
            pk=option_id
        ).first()
        
        if option is None:
            raise ValidationError(
                "Варіант відповіді не належить цьому кроку завдання"
            )
        
        return option.is_correct
    
    def _get_prompt(self, question: Question) -> dict:
        
        # Отбираем QuestionImage-ы вопроса
        # Для того чтобы перемешать изображений (если они есть) с текстом, в случайном порядке
        images = [
            image for image in question.images.all()
            if not image.is_placeholder and image.image
        ]
        
        # Из вариантов записи вопроса (текстом или картинкой) 
        # случайно выбираем один из них
        prompt_choice = random.choice(["text"] + images)
        
        # Если попался текст, то на странице будет отображен текст вопроса
        if prompt_choice == "text":
            return {"kind": "text", "text": question.text}
        
        # Если попалась картинка, передаем на нее ссылку (media-url)
        # В браузере, в таком случае, будет отображена картинка
        return {"kind": "image", "url": prompt_choice.image.url}
