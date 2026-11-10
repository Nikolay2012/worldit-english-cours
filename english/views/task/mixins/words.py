"""
Миксин контекста страницы задания типа "Слова"

Подключается к EnglishTaskView и вызывается через _get_type_context()
когда у задания тип "words"

Возвращает данные для шаблонов:
-can_edit_words - может ли редактировать список слов в боковой панели (персонал)
-can_open_words_list - показывать ли кнопку «Список слів» (есть шаги)
-import_title, import_text - заголовок и абзацы режима загрузки
-default_title, default_description - заголовок и описание модалки загрузки

Тексты пока захардкожены, позже они будут приходить из настроек задания
"""

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
