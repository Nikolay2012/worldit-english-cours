"""
Эндпоинт создания и редактирования одного предложения в задании типа "Предложения"

Используется модалкой upload_csv_modal (список предложений после импорта)
Доступ: только админ

Два маршрута на один класс:
-POST /tasks/<task_id>/sentences/ - без step_id - создание предложения
-POST /tasks/<task_id>/sentences/<step_id>/ - со step_id - редактирование предложения

Тело запроса - JSON:
-«Скласти речення» - {"answer", "prompt"}
-«Доповнити речення» - {"answer", "prompt", "gaps", "inserts"}
    -gaps - позиции слов-пропусков в токенах предложения
    -inserts - вставки: нулевой артикль или знак (, . - : ;) с позицией

Логика - в SentenceStepService:
-.create() - добавляет предложение в конец задания (следующий order)
-.update() - перезаписывает предложение и пересоздаёт его токены
-Вариант предложения должен совпадать с вариантом остальных предложений задания

Ответы:
-200 - {"ok": true, "data": {"sentences": [...], "is_fill", "required_correct_answers"}}
полный список предложений задания для перерисовки списка в модалке
-400 - тело не JSON или не объект, ошибки проверки предложения (ValidationError)
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
    required_type(['admin']), 
    name="dispatch"
)
class SentenceEndpoint(View):
    
    def post(
        self,
        request: HttpRequest,
        task_id: int,
        step_id: int | None = None
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
            if step_id is None:
                sentences_list = service.create(
                    task_id=task_id,
                    data=data
                )
            else:
                sentences_list = service.update(
                    task_id=task_id,
                    data=data,
                    step_id=step_id
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
            {"ok": True, "data": sentences_list},
            status=200
        )
