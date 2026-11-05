"""
Эндпоинт ответа на шаг задания

Используется на странице прохождения задания:
когда пользователь выбирает вариант ответа,
клиент (task_runner.js) отправляет ответ сюда

Маршрут:
POST /courses/english/api/tasks/<task_id>/steps/<step_id>/answer/

Доступ - админ, ментор или студент (required_type(["admin", "student"]))

В запросе (JSON) передаётся ответ пользователя
Для шага с вопросом (kind = "question"): {"option_id": ...}
Что внутри ответа, знает только обработчик шага - эндпоинт его не разбирает

Ответы:
-200 {"ok": true, "data": {"is_correct": bool, "progress": {...}}}
    правильный вариант не возвращается, только верен ли выбранный
-400 {"ok": false, "error": "..."} - некорректный JSON, некорректный вариант ответа
    или вариант не принадлежит этому шагу
-404 {"ok": false, "error": "..."} - задание не найдено или шаг не из этого задания

Проверку ответа (и для студента - запись ответа и прогресса)
выполняет TaskRunner
Эндпоинт только разбирает JSON
и переводит ошибки ядра в HTTP-ответы
"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner.task_runner import TaskRunner


@method_decorator(
    required_type(['admin', 'student']), 
    name="dispatch"
)
class StepAnswerEndpoint(View):
    http_method_names = ["post"]
    
    def post(
            self, 
            request: HttpRequest, 
            task_id: int, 
            step_id: int
        ) -> JsonResponse:
        
        try:
            data = json.loads(
                request.body
            )
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
        
        try:
            result = TaskRunner(
                task_id=task_id,
                user=request.user
            ).answer(
                step_id=step_id,
                data=data
            )
            
        except NotFoundError as error:
            return JsonResponse(
                {"ok": False, "error": error.message},
                status=404
            )
        
        except ValidationError as error:
            return JsonResponse(
                {"ok": False, "error": error.message},
                status=400
            )
        
        
        return JsonResponse(
            {"ok": True, "data": result},
            status=200
        )
