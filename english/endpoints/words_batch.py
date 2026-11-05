"""

"""

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.word_steps import WordStepService


@method_decorator(
    required_type(["admin"]),
    name="dispatch"
)
class WordsBatchEndpoint(View):
    http_method_names = ["post"]
    
    def post(
            self,
            request: HttpRequest,
            task_id: int
        ) -> JsonResponse:
        
        try:
            WordStepService().save_batch(
                task_id=task_id,
                changes_json=request.POST.get("changes"),
                files=request.FILES
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
            
        return JsonResponse({"ok": True}, status=200)
