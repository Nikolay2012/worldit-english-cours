"""

"""

from django.utils.decorators import method_decorator
from django.http import HttpRequest, JsonResponse
from django.views import View

from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner import TaskRunner


@method_decorator(
    required_type(["admin", "student"]),
    name="dispatch"
)
class WordsProgressEndpoint(View):
    http_method_names = ["get"]
    
    def get(
        self,
        request: HttpRequest,
        task_id: int
    ) -> JsonResponse:
        
        try:
            data = TaskRunner(
                task_id=task_id,
                user=request.user
            ).get_words_progress()
            
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
