import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from WorldIT.decorators import required_type
from english.services.lesson_tasks import update_lesson_tasks
from english.services.exceptions import ValidationError, NotFoundError


@require_http_methods(["PATCH"])
@required_type(['admin'])
def update_lesson_tasks_endpoint(
        request: HttpRequest, 
        lesson_id: int
    ) -> JsonResponse:
    
    try:
        data: dict = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"ok": False, "error": "Некоректний JSON"}, 
            status=400
        )
    
    if not isinstance(data, dict):
        return JsonResponse(
            {"ok": False, "error": "Очікується JSON-обʼєкт"}, 
            status=400
        )
    
    renamed_tasks = data.get("renamed", [])
    deleted_tasks = data.get("deleted", [])
    
    try: 
        update_lesson_tasks(
            lesson_id=lesson_id,
            renamed=renamed_tasks,
            deleted=deleted_tasks
        )
    except ValidationError as error:
        return JsonResponse(
            {"ok": False, "error": error.message}, 
            status=400
        )
    
    except NotFoundError as error:
        return JsonResponse(
            {"ok": False, "error": error.message}, 
            status=404
        )
    
    return JsonResponse({"ok": True}, status=200)
