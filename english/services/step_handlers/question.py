"""
Обработчик шага задания с вопросом и вариантами ответа (kind = "question")

Используется ядром прохождения TaskRunner через реестр StepHandlerRegistry
Реализует методы интерфейса StepHandler:
-.get_step_data() - сборка данных шага для клиента
-.check() - проверка ответа пользователя

Сейчас используется в заданиях типа "Слова"
В дальнейшем подойдёт и для чтения и видео:
у них отличается только способ подачи вопроса (prompt), а проверка ответа та же

Сборка шага - метод .get_step_data():
-Варианты ответа перемешиваются на сервере
-Клиенту уходят только id и текст вариантов, без is_correct
-Вид вопроса выбирается случайно - метод ._get_prompt():
    -текстом (слово)
    -или одной из картинок вопроса, которые не плейсхолдеры
    если у вопроса нет настоящих картинок - вопрос всегда текстом

Проверка ответа - метод .check():
-От клиента приходит {"option_id": ...}
-Вариант ищется только среди вариантов этого вопроса
-Возвращается is_correct выбранного варианта

Из ошибок, может подниматься ValidationError:
-option_id не передан или не число
-вариант ответа не принадлежит вопросу этого шага

.save_answer_details() - запись выбранного варианта в ответ студента (selected_options)
"""

import random

from english.models.answer_option import AnswerOption
from english.models.english_task_step import EnglishTaskStep
from english.models.question import Question
from english.models.student_answer import StudentAnswer
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
        
        return self._get_option(
            step=step, 
            data=data
        ).is_correct
    
    def save_answer_details(
            self, 
            answer: StudentAnswer, 
            step: EnglishTaskStep, 
            data: dict
        ):
        
        answer.selected_options.set(
            [
                self._get_option(step=step, data=data)
            ]
        )
    
    def _get_option(self, step: EnglishTaskStep, data: dict) -> AnswerOption:
        
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
            
        return option
    
    def _get_prompt(self, question: Question) -> dict:
        
        # Отбираем QuestionImage-ы вопроса
        # Для того чтобы перемешать изображений (если они есть) с текстом, в случайном порядке
        images = [
            image for image in question.images.all()
            if not image.is_placeholder and image.image
        ]
        
        # Из вариантов записи вопроса (текстом или картинкой) 
        # случайно выбираем один из них
        prompt_choice = random.choice(["text", "text"] + images)
        
        # Если попался текст, то на странице будет отображен текст вопроса
        if prompt_choice == "text":
            return {"kind": "text", "text": question.text}
        
        # Если попалась картинка, передаем на нее ссылку (media-url)
        # В браузере, в таком случае, будет отображена картинка
        return {"kind": "image", "url": prompt_choice.image.url}
