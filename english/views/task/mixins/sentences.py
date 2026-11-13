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
            "can_open_theory": True,
            "import_title": "Завантажте список речень",
            "import_text": [
                "Увага!",
                "Документ типу csv має чітко відповідати шаблону.",
                "Завантажте будь-ласка файл та перевірте правильність заповнення вашого документу.",
            ],
            "default_title": "Завантажте список речень",
            "default_description": "Завантажте документ зі списком речень для цього уроку.",
            "theory_blocks": [
                {"type": "title", "text": "Урок 1"},
                {"type": "text", "parts": ["На першому уроці ми попрацюємо з дієсловами у формі простого часу, а саме - у теперішньому часі."]},
                {"type": "text", "parts": ["Розберемося як побудувати ствердну форму речення теперішнього часу."]},
                {"type": "title", "text": "Теперішній час", "secondary": True},
                {"type": "text", "parts": ["Ствердна форма речення формується з займенника, а потім додаються дієслова."]},
                {"type": "text", "parts": [
                    "Якщо застосовується займенник ",
                    {"text": "HE", "accent": True},
                    " (він), ",
                    {"text": "SHE", "accent": True},
                    " (вона) або ",
                    {"text": "IT", "accent": True},
                    " (це), то до дієслова додається закінчення -",
                    {"text": "S", "accent": True},
                    ".",
                ]},
                {
                    "type": "image",
                    "src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTr7Q2-iOUXeta4efD3d8FAPLTOfSN1lKRhOGJInoa6mA&s=10",
                    "alt": "Теперішній час: ствердна форма",
                },
            ]
        }
