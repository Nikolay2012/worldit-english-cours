"""

"""

from django.core import files
from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ConflictError, ValidationError
from english.services.word_steps import WordStepService


@method_decorator(
    required_type(['admin', 'mentor']), 
    name="dispatch"
)
class WordEndpoint(View):
    
    def post(
        self,
        request: HttpRequest,
        task_id: int,
        step_id: int | None = None
    ) -> JsonResponse:
    
        service = WordStepService()
        
        try:
            if step_id is None:
                words_list = service.create(
                    task_id=task_id,
                    data=request.POST,
                    files=request.FILES
                )
            else:
                words_list = service.update(
                    task_id=task_id,
                    step_id=step_id,
                    data=request.POST,
                    files=request.FILES
                )
                
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
        
        except ValidationError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=400
            )
        
        return JsonResponse(
            {"ok": True, "data": words_list},
            status=200
        )
