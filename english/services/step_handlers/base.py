"""
Базовый обработчик шага задания

Задаёт общий интерфейс для всех видов шагов:
каждый вид шага (вопрос, предложение и т.д.) наследует этот класс
и реализует оба метода по-своему

Методы интерфейса:
-.get_step_data(step) - собрать данные шага для отправки клиенту
-.check(step, data) - проверить ответ пользователя, вернуть True или False

Если наследник не реализовал метод,
при вызове поднимется NotImplementedError

Ядро прохождения TaskRunner работает только с этим интерфейсом
и не знает, какой именно обработчик перед ним
Конкретный обработчик выбирается в StepHandlerRegistry по виду шага (kind)

Реализации:
-QuestionHandler - шаг с вопросом и вариантами ответа (kind = "question")
"""

from english.models.english_task_step import EnglishTaskStep
from english.models.student_answer import StudentAnswer


class StepHandler:
    
    # Метод получения данных шага, если угодно «сериализации»
    # Реализуется QuestioHandler, SentencesHandler и прочими
    def get_step_data(self, step: EnglishTaskStep) -> dict:
        raise NotImplementedError
    
    # Метод анализа предоставленного пользователем (админом/студентом/ментором) ответа
    # Реализуется QuestioHandler, SentencesHandler и прочими
    def check(self, step: EnglishTaskStep, data: dict) -> bool:
        raise NotImplementedError
    
    # Метод записи данных ответа студента, 
    # а именно - с какими AnswerOption's связан StudentAnswer
    def save_answer_details(
            self, 
            answer: StudentAnswer, 
            step: EnglishTaskStep, 
            data: dict
        ):
        
        raise NotImplementedError
