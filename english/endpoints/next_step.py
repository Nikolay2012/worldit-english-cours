"""

"""

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
