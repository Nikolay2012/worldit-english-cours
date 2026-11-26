"""
Реестр обработчиков шагов задания

Выбирает обработчик по виду шага (поле kind у EnglishTaskStep)
Используется ядром прохождения TaskRunner

Использование:
StepHandlerRegistry().get_handler(kind) - возвращает объект обработчика

Зарегистрированные обработчики (STEP_HANDLERS):
-"question" - QuestionHandler, вопрос с вариантами ответа (задания "Слова")
-"sentence" - SentenceHandler, предложение (задания "Речення": "Скласти" и "Доповнити")

Обработчик (наследник StepHandler) знает, как:
-собрать данные шага для клиента - метод .get_step_data()
-проверить ответ пользователя - метод .check()
-записать подробности ответа студента - метод .save_answer_details()

Ядро TaskRunner не знает, как устроен конкретный шаг,
оно получает обработчик из реестра и вызывает его методы

Чтобы добавить новый вид шага (например, для чтения или видео),
достаточно написать его обработчик и добавить в STEP_HANDLERS

Из ошибок, может подниматься ValidationError - для вида шага нет обработчика
"""

from english.services.exceptions import ValidationError
from english.services.step_handlers.base import StepHandler
from english.services.step_handlers.question import QuestionHandler
from english.services.step_handlers.sentence import SentenceHandler


class StepHandlerRegistry:
    def __init__(self):
        
        self.STEP_HANDLERS = {
            "question": QuestionHandler,
            "sentence": SentenceHandler
        }
    
    def get_handler(self, kind: str) -> StepHandler:
        
        handler_class = self.STEP_HANDLERS.get(kind)
        
        if handler_class is None:
            raise ValidationError("Невідомий тип кроку")
        
        return handler_class()
