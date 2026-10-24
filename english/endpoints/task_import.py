"""

"""

import json
import time

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type


# Создавать задание и указывать его содержимое может либо админ, 
# либо ментор
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
        
        # print(request.POST)
        # print(request.FILES)
        # print(task_id)
        
        # time.sleep(5)
        
        return JsonResponse({"ok": True}, status=200)

