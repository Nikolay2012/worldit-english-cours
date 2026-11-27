"""
Миксин контекста страницы задания типа "Речення"

Подключается к EnglishTaskView и вызывается через _get_type_context(),
когда у задания тип "sentences"

Возвращает данные для шаблонов - метод ._get_sentences_context(has_steps):
-can_open_answers_list - показывать ли кнопки шапки задания (есть шаги)
-can_edit_sentences - персонал (admin) через self._is_staff():
    -True - кнопка «Список речень», панель с редактированием и созданием предложений
    -False - кнопка «Історія відповідей», панель только с правильно пройденными предложениями
-import_title, import_text - заголовок и абзацы режима загрузки
-default_title, default_description - заголовок и описание модалки загрузки
-delete_confirm_text - текст подтверждения удаления списка предложений

Тексты пока захардкожены, позже они будут приходить из настроек задания
"""

from english.views.task.mixins.base import TaskContentBase


class SentencesTaskContentMixin(TaskContentBase):
    
    def _get_sentences_context(self, has_steps: bool):
        
        return {
            "can_open_answers_list": has_steps,
            "can_edit_sentences": self._is_staff(),
            "import_title": "Завантажте список речень",
            "import_text": [
                "Увага!",
                "Документ типу csv має чітко відповідати шаблону.",
                "Завантажте будь-ласка файл та перевірте правильність заповнення вашого документу.",
            ],
            "default_title": "Завантажте список речень",
            "default_description": "Завантажте документ зі списком речень для цього уроку.",
            "delete_confirm_text": "Усі речення та переклади цього завдання буде видалено. Цю дію не можна скасувати."
        }
