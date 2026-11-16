"""

"""

from english.services.task_importers.sentence import SentenceImporter


class SentenceStepService(SentenceImporter):
    def __init__(self):
        super().__init__()
        
        
    
    def create(
            self,
            task_id: int, 
            data: dict
        ) -> dict[str, list|int]:
        
        return {
            "sentences": [
                {
                    "step_id": 1,
                    "answer": "answer1",
                    "prompt": "prompt1",
                    "template": "template1"
                }
            ],
            "required_correct_answers": self.REQUIRED_CORRECT_ANSWERS
        }
    
    def update(
            self,
            task_id: int, 
            data: dict
        ) -> dict[str, list|int]:
        
        return {
            "sentences": [
                {
                    "step_id": 1,
                    "answer": "answer1",
                    "prompt": "prompt1",
                    "template": "template1"
                }
            ],
            "required_correct_answers": self.REQUIRED_CORRECT_ANSWERS
        }
