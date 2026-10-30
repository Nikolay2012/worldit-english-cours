"""

"""

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type


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
        
        return JsonResponse({
            "ok": True,
            "data": {
                "is_correct": True,
                "progress": {
                    "percent": 25,
                    "is_completed": False
                }
            }
        })
