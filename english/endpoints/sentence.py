"""

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
