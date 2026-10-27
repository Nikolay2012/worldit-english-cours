"""
Эндпоинт сохранения изменений заданий урока

Используется на странице модуля в режиме редактирования урока:
по кнопке «Зберегти» клиент одним запросом отправляет
переименованные и удалённые задания

Маршрут:
PATCH /courses/english/api/lessons/<lesson_id>/tasks/

Доступ - только админ (required_type(["admin"]))

В запросе (JSON) передаётся:
{
    "renamed": [{"taskId": "12", "name": "Нова назва"}, ...],
    "deleted": ["15", "16"]
}
Оба поля можно не передавать, тогда они считаются пустыми списками

Ответы:
-200 {"ok": true} - изменения сохранены
-400 {"ok": false, "error": "..."} - некорректный JSON или данные не прошли проверку
-404 {"ok": false, "error": "..."} - урок не найден или задания не из этого урока

Вся работа с данными находится в LessonTasksService
Эндпоинт только разбирает запрос
и переводит ошибки сервиса в HTTP-ответы
"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.lesson_tasks import LessonTasksService
from english.services.exceptions import ValidationError, NotFoundError


# Изменять (изменять/удалять) задания может только администратор платформы
@method_decorator(
    required_type(['admin']), 
    name="dispatch"
)
class LessonTasksEndpoint(View):
    
    def patch(
        self,
        request: HttpRequest, 
        lesson_id: int
    ) -> JsonResponse:
        
        try:
            data: dict = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"ok": False, "error": "Некоректний JSON"}, 
                status=400
            )
        
        if not isinstance(data, dict):
            return JsonResponse(
                {"ok": False, "error": "Очікується JSON-обʼєкт"}, 
                status=400
            )
        
        renamed_tasks = data.get("renamed", [])
        deleted_tasks = data.get("deleted", [])
        
        try: 
            LessonTasksService(
                lesson_id=lesson_id,
                renamed=renamed_tasks,
                deleted=deleted_tasks
            ).update()
        except ValidationError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=400
            )
        
        except NotFoundError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=404
            )
        
        return JsonResponse({"ok": True}, status=200)
