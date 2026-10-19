import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from WorldIT.decorators import required_type


@require_http_methods(["PATCH"])
@required_type(['admin'])
def update_lesson_tasks_endpoint(
        request: HttpRequest, 
        lesson_id: int
    ):
    
    data = json.loads(request.body)
    
    print(data)
    
    return JsonResponse({"data": "good"}, status=200)
