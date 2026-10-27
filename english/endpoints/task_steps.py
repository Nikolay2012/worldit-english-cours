"""

"""

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ConflictError
from english.services.task_steps import TaskStepsService


@method_decorator(
    required_type(["admin", "mentor"]), 
    name="dispatch"
)
class TaskStepsEndpoint(View):
    http_method_names = ["delete"]
    
    def delete(
            self, 
            request: HttpRequest, 
            task_id: int
        ) -> JsonResponse:
        
        try:
            TaskStepsService(
                task_id=task_id
            ).delete_all()
            
        except NotFoundError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=404
            )
        
        except ConflictError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=409
            )
        
        return JsonResponse({"ok": True}, status=200)
