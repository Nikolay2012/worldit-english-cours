"""
Эндпоинт списка слов задания с прогрессом по каждому слову
для боковой панели «Список слів»

Маршрут:
GET /courses/english/api/tasks/<task_id>/words-progress/ (name="english:api:api_words_progress")

Доступ - admin, student

Данные собирает TaskRunner.get_words_progress():
-слова задания сгруппированы по категориям
-у каждого слова - сколько у студента правильных ответов на него
-персонал (admin) видит слова без прогресса (правильных ответов 0)
-админ по этим данным ещё и редактирует слова в панели (step_id, картинки)

Задание ищется только среди активных заданий курса английского,
архивированное задание даёт 404

Ответы:
-200 - {"ok": True, "data": {
    "categories": [{"category", "words": [{"step_id", "text", "translation", "images", "correct_count"}]}],
    "required_correct_answers": сколько правильных ответов нужно на слово (6)
}}
-400 - {"ok": False, "error": ...} - неизвестный вид шага
-404 - {"ok": False, "error": ...} - задание не найдено
"""

from django.utils.decorators import method_decorator
from django.http import HttpRequest, JsonResponse
from django.views import View

from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.task_runner.task_runner import TaskRunner


@method_decorator(
    required_type(["admin", "student"]),
    name="dispatch"
)
class WordsProgressEndpoint(View):
    http_method_names = ["get"]
    
    def get(
        self,
        request: HttpRequest,
        task_id: int
    ) -> JsonResponse:
        
        try:
            data = TaskRunner(
                task_id=task_id,
                user=request.user
            ).get_words_progress()
            
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
            
        return JsonResponse(
            {"ok": True, "data": data},
            status=200
        )
