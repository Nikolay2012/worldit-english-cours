"""
Эндпоинт пакетного сохранения предложений из боковой панели «Список речень»

Используется кнопкой «Зберегти» в панели на странице задания типа "Предложения"
Доступ: только админ

POST /tasks/<task_id>/sentences/batch/ - имя маршрута api_sentences_batch

Клиент копит изменения в панели и отправляет их одним запросом,
чтобы каждое мелкое или случайное создание/редактирование не вызывало запрос

Тело запроса - JSON: {"changes": [...]}
Одно изменение - {"key", "mode", "step_id", "data"}:
-key - ключ строки в панели: step_id предложения или new-1, new-2... у новых
-mode - "create" (новое предложение) или "edit" (редактирование)
-step_id - шаг предложения при "edit", null при "create"
-data - то же тело, что модалка upload_csv_modal отправляет на SentenceEndpoint:
    -«Скласти речення» - {"answer", "prompt"}
    -«Доповнити речення» - {"answer", "prompt", "gaps", "inserts"}

Логика - SentenceStepService.save_batch():
-Изменения применяются по очереди через .create() и .update()
-Всё в одной транзакции: если хоть одно предложение не прошло проверку,
не сохраняется ни одно
-В тексте ошибки указывается предложение, на котором она возникла

Ответы:
-200 - {"ok": true} - клиент после сохранения перезагружает страницу
-400 - тело не JSON, пустой или некорректный список изменений,
неизвестный mode, ошибки проверки предложения (ValidationError)
-404 - задание или предложение не найдено (NotFoundError)
"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.sentence_steps import SentenceStepService


@method_decorator(
    required_type(["admin"]),
    name="dispatch"
)
class SentencesBatchEndpoint(View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest, task_id: int) -> JsonResponse:
        
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {"ok": False, "error": "Некоректні дані змін"},
                status=400
            )
        
        try:
            SentenceStepService().save_batch(
                task_id=task_id,
                changes=body.get("changes") if isinstance(body, dict) else None
            )
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
        
        return JsonResponse({"ok": True}, status=200)
