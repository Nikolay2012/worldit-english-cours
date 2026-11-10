
from english.views.task.mixins.base import TaskContentBase

class SentencesTaskContentMixin(TaskContentBase):
    
    # --
    # временная часть для шаблона задания типа "предложения"
    # пока ещё не готов парсинг
    PREVIEW_COMPONENT = "english/components/task/sentence_preview.html"
    # --
    
    def _get_sentences_context(self, has_steps: bool):
        
        return {
            "can_open_theory": True,
            "import_title": "Завантажте список речень",
            "import_text": [
                "Увага!",
                "Документ типу csv має чітко відповідати шаблону.",
                "Завантажте будь-ласка файл та перевірте правильність заповнення вашого документу.",
            ],
            "default_title": "Завантажте список речень",
            "default_description": "Завантажте документ зі списком речень для цього уроку."
        }
