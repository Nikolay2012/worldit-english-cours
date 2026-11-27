"""

"""

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator

from WorldIT.decorators import required_type


@method_decorator(
    required_type(["student", "admin"]),
    name="dispatch"
)
class SentencesProgressEndpoint(View):
    http_method_names = ["get"]

    def get(self, request: HttpRequest, task_id: int) -> JsonResponse:
        return JsonResponse(
            {"ok": True, "data": {"sentences": []}},
            status=200
        )
