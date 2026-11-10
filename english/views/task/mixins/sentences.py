
from english.views.task.mixins.base import TaskContentBase

class SentencesTaskContentMixin(TaskContentBase):
    
    def _get_sentences_context(self, has_steps: bool):
        
        return {
            "import_title": "Завантажте список речень",
            "import_text": [
                "Увага!",
                "Документ типу csv має чітко відповідати шаблону.",
                "Завантажте будь-ласка файл та перевірте правильність заповнення вашого документу.",
            ],
            "default_title": "Завантажте список речень",
            "default_description": "Завантажте документ зі списком речень для цього уроку."
        }
