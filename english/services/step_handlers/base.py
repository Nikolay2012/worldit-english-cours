"""

"""

from english.models.english_task_step import EnglishTaskStep


class StepHandler:
    
    # Метод получения данных шага, если угодно «сериализации»
    # Реализуется QuestioHandler, SentencesHandler и прочими
    def get_step_data(self, step: EnglishTaskStep) -> dict:
        raise NotImplementedError
    
    # Метод анализа предоставленного пользователем (админом/студентом/ментором) ответа
    # Реализуется QuestioHandler, SentencesHandler и прочими
    def check(self, step: EnglishTaskStep, data: dict) -> bool:
        raise NotImplementedError
