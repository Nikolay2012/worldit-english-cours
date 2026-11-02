"""
Эндпоинт получения следующего шага задания

Используется на странице прохождения задания:
клиент (task_runner.js) запрашивает здесь первый шаг при открытии задания
и каждый следующий шаг после ответа

Маршрут:
GET /courses/english/api/tasks/<task_id>/next-step/
GET /courses/english/api/tasks/<task_id>/next-step/?after=<step_id>

Доступ - админ, ментор или студент (required_type(["admin", "mentor", "student"]))

Параметр after - id шага, на который только что ответили
Персоналу по нему отдаётся следующий шаг по порядку
Без after - первый шаг задания

Ответы:
-200 {"ok": true, "data": {"step": {...} или null, "progress": {...}}}
    step = null - задание пройдено до конца
    в step нет правильности вариантов ответа (is_correct)
-400 {"ok": false, "error": "..."} - after не число или неизвестный вид шага
-404 {"ok": false, "error": "..."} - задание или шаг after не найдены в этом задании

Выбор шага и сборку его данных выполняет TaskRunner
Эндпоинт только разбирает параметр after
и переводит ошибки ядра в HTTP-ответы
"""

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner import TaskRunner


@method_decorator(
    required_type(['admin', 'student']), 
    name="dispatch"
)
class NextStepEndpoint(View):
    http_method_names = ["get"]
    
    def get(
            self, 
            request: HttpRequest, 
            task_id: int
        ) -> JsonResponse:
        
        # текущий шаг
        after = request.GET.get("after")
        
        try:
            after_step_id = int(after) if after else None
        except Exception:
            return JsonResponse(
                {"ok": False, "error": "Некоректний id кроку завдання"},
                status=400
            )
        
        try:
            data = TaskRunner(
                task_id=task_id,
                user=request.user
            ).get_next_step(
                after_step_id=after_step_id
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
            {"ok": True, "data": data},
            status=200
        )
