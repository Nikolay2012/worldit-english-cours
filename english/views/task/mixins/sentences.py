"""
Миксин контекста страницы задания типа "Предложения"

Подключается к EnglishTaskView и вызывается через _get_type_context()
когда у задания тип "sentences"

Возвращает данные для шаблонов:
-can_open_theory - показывать ли кнопку «Допомога» (теория)
-import_title, import_text - заголовок и абзацы режима загрузки
-default_title, default_description - заголовок и описание модалки загрузки
-theory_blocks - блоки модалки теории (title, text, image)

Временно:
-PREVIEW_COMPONENT - шаблон превью вместо страницы прохождения,
пока нет парсинга и шагов. Удалить вместе с проверкой в _get_content_component()
-theory_blocks захардкожены, позже придут из модели Theory

Тексты и блоки пока захардкожены, позже они будут приходить из настроек задания
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
