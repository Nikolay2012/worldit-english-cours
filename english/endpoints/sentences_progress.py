"""

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
