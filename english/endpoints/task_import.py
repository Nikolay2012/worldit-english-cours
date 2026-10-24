"""

"""

import json

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.lesson_tasks import LessonTasksService
from english.services.exceptions import ValidationError, NotFoundError


@method_decorator(
    required_type(['admin', 'mentor']), 
    name="dispatch"
)
class TaskImportEndpoint(View):
    http_method_names = ["post"]
    
    def post(
        self,
        request: HttpRequest, 
        task_id: int
    ) -> JsonResponse:
        
        return JsonResponse({"ok": True}, status=200)
