"""
Эндпоинт импорта содержимого задания из CSV-файла.

Используется на странице пустого задания: администратор или ментор
выбирает CSV-файл в модалке «Завантаження списку слів», и файл
отправляется сюда по кнопке «Продовжити».

Маршрут:
    POST /courses/english/api/tasks/<task_id>/import/

Доступ:
    администратор или ментор (required_type(["admin", "mentor"])).

Тело запроса (multipart/form-data):
    file — CSV-файл, UTF-8, не больше 1 МБ.

Ответы:
    200  {"ok": true, "data": {...}}     содержимое задания создано
    400  {"ok": false, "error": "..."}   нет файла, не .csv, некорректный размер или ошибка в строках файла
    404  {"ok": false, "error": "..."}   задание не найдено или не относится к курсу English
    409  {"ok": false, "error": "..."}   у задания уже есть шаги, импорт возможен только в пустое задание

Разбор файла и запись в базу выполняет импортер для типа задания
(english.services.importers). Эндпоинт проверяет запрос и
переводит исключения импортера в HTTP-ответы.

сейчас эндпоинт — заглушка, всегда возвращает {"ok": true}.
"""

import json
import time

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type


# Создавать задание и указывать его содержимое может либо админ, 
# либо ментор
@method_decorator(
    required_type(['admin', 'mentor']), 
    name="dispatch"
)
class TaskImportEndpoint(View):
    http_method_names = ["post"]
    
    def post(
        self,
        request: HttpRequest, 
        task_id: int
    ) -> JsonResponse:
        
        # print(request.POST)
        # print(request.FILES)
        # print(task_id)
        
        # time.sleep(5)
        
        return JsonResponse({"ok": True}, status=200)

