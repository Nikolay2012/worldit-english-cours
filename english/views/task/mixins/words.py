
from english.views.task.mixins.base import TaskContentBase


class WordsTaskContentMixin(TaskContentBase):
    
    def _get_words_context(self, has_steps: bool):
        
        return {
            "can_edit_words": self._is_staff(),
            "can_open_words_list": has_steps,
            "import_title": "Завантажте список слів",
            "import_text": ["Завантажте документ зі списком слів."],
            "default_title": "Завантаження списку слів",
            "default_description": "Завантажте документ зі списком слів для цього уроку."
        }
