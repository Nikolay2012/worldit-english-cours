"""

"""

from english.services.exceptions import ValidationError
from english.services.step_handlers.base import StepHandler
from english.services.step_handlers.question import QuestionHandler


class StepHandlerRegistry:
    def __init__(self):
        
        self.STEP_HANDLERS = {
            "question": QuestionHandler
        }
    
    def get_handler(self, kind: str) -> StepHandler:
        
        handler_class = self.STEP_HANDLERS.get(kind)
        
        if handler_class is None:
            return ValidationError("Невідомий тип кроку")
        
        return handler_class()
