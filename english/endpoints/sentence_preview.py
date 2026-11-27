"""
Эндпоинт превью предложения варианта «Доповнити речення»

Используется модалкой upload_csv_modal по кнопке «Далі»
(переход от ввода предложения к выбору пропусков)
Работает и для модалки списка после импорта, и для модалки из боковой панели
Доступ: только админ
Ничего не сохраняет в БД - только разбивает предложение на токены

POST /tasks/<task_id>/sentences/preview/

Тело запроса - JSON: {"answer", "prompt"}

Логика - SentenceStepService.sentence_preview():
-Задание должно содержать предложения с пропусками (вариант «Доповнити»)
-Предложение проверяется и разбивается на токены так же, как при сохранении

Данные одного токена:
-index - позиция токена в предложении (по ней клиент отмечает пропуски и вставки)
-text - текст токена
-is_word - слово или число (true) или знак (false)
знаки не могут быть пропусками, на клиенте они неактивны

Ответы:
-200 - {"ok": true, "data": {"tokens": [{"index", "text", "is_word"}]}}
-400 - тело не JSON или не объект, задание без пропусков,
ошибки проверки предложения (ValidationError)
-404 - задание не найдено (NotFoundError)
"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.sentence_steps import SentenceStepService


@method_decorator(
    required_type(['admin']), 
    name="dispatch"
)
class SentencePreviewEndpoint(View):
    
    def post(
        self,
        request: HttpRequest,
        task_id: int,
    ) -> JsonResponse:
        
        service = SentenceStepService()

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"ok": False, "error": "Некоректні дані запиту"},
                status=400
            )
        
        if not isinstance(data, dict):
            return JsonResponse(
                {"ok": False, "error": "Некоректні дані запиту"},
                status=400
            )
        
        try:
            sentence_tokens = service.sentence_preview(
                task_id=task_id,
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
            {"ok": True, "data":sentence_tokens },
            status=200
        )
