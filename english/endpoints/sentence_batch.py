"""

"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View

from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.sentence_steps import SentenceStepService


@method_decorator(
    required_type(["admin"]),
    name="dispatch"
)
class SentencesBatchEndpoint(View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest, task_id: int) -> JsonResponse:
        
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {"ok": False, "error": "Некоректні дані змін"},
                status=400
            )
        
        try:
            SentenceStepService().save_batch(
                task_id=task_id,
                changes=body.get("changes") if isinstance(body, dict) else None
            )
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
        
        return JsonResponse({"ok": True}, status=200)
