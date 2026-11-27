"""
Эндпоинт боковой панели предложений на странице задания типа "Предложения"

GET /tasks/<task_id>/sentences-progress/ - имя маршрута api_sentences_progress
Доступ: студент и админ

Данные собирает TaskRunner.get_sentences_progress():
-Админ - «Список речень»: все предложения задания по порядку (order)
-Студент - «Історія відповідей»: только предложения с правильным ответом,
по порядку первого правильного ответа

Данные одного предложения собирает SentenceHandler.get_list_item():
-step_id, answer, prompt, template
-gaps и zero_gaps - позиции пропусков и нулевых артиклей
(нужны модалке редактирования у админа)
-parts - куски предложения для отображения в панели:
    -{"kind": "text", "text"} - обычный текст
    -{"kind": "gap", "text"} - слово-пропуск (подчёркивается)
    -{"kind": "zero"} - нулевой артикль (___)

Ответы:
-200 - {"ok": true, "data": {"sentences": [...]}}
-404 - задание не найдено или неактивно (NotFoundError)
-400 - задание не типа "Предложения" (ValidationError)
"""

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator

from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner.task_runner import TaskRunner


@method_decorator(
    required_type(["student", "admin"]),
    name="dispatch"
)
class SentencesProgressEndpoint(View):
    http_method_names = ["get"]

    def get(self, request: HttpRequest, task_id: int) -> JsonResponse:
        
        try:
            data = TaskRunner(
                task_id=task_id,
                user=request.user
            ).get_sentences_progress()
        except NotFoundError as error:
            return JsonResponse(
                {"ok": False, "error": str(error)},
                status=404
            )
        except ValidationError as error:
            return JsonResponse(
                {"ok": False, "error": str(error)},
                status=400
            )
        
        return JsonResponse(
            {"ok": True, "data": data},
            status=200
        )
