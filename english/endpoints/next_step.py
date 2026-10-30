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
class NextStepEndpoint(View):
    
    def get(
            self, 
            request: HttpRequest, 
            task_id: int
        ) -> JsonResponse:
        
        return JsonResponse({
            "ok": True,
            "data": {
                "step": {
                    "id": 1,
                    "kind": "question",
                    "prompt": {
                        "kind": "text",
                        "text": "she"
                    },
                    "options": [
                        {"id": 1, "text": "Він"},
                        {"id": 2, "text": "Ти"},
                        {"id": 3, "text": "Вона"},
                        {"id": 4, "text": "Ми"},
                        {"id": 5, "text": "Ви"},
                        {"id": 6, "text": "Вони"}
                    ]
                },
                "progress": {
                    "percent": 20,
                    "is_completed": False
                }
            }
        })
