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
