"""
Базовый класс для миксинов контекста страницы задания

Нужен только для подсказок IDE и проверки типов
В рантайме ничего не делает: атрибуты и методы даёт EnglishTaskView

Миксин, который наследует этот класс, может использовать:
-self.object - задание (EnglishTask)
-self.request - текущий запрос
-self._is_staff() - персонал (admin)

Миксины собирают только свою часть контекста,
например WordsTaskContentMixin._get_words_context()
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

    from english.models import EnglishTask


class TaskContentBase:
    if TYPE_CHECKING:
        object: "EnglishTask"
        request: "HttpRequest"

        def _is_staff(self) -> bool:
            ...
