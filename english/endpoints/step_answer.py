"""

"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner import TaskRunner


@method_decorator(
    required_type(['admin', 'mentor', 'student']), 
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
