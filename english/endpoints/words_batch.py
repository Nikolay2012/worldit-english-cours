"""
Эндпоинт сохранения всех изменений списка слов из боковой панели «Список слів»

Маршрут:
POST /courses/english/api/tasks/<task_id>/words/batch/ (name="english:api:api_words_batch")

Доступ - admin

Изменения копятся на клиенте и приходят одним запросом
по кнопке «Зберегти» в боковой панели

Что принимает (multipart/form-data):
-changes - JSON-строка со списком изменений
каждое изменение: {"key", "mode", "step_id", "category", "word", "translation", "removed_images"}
    -mode - "create" (новое слово) или "edit" (редактирование)
    -key - ключ изменения на клиенте, по нему ищутся картинки
-image_<key>_<order> - новые картинки слов (необязательно)

Сохранение выполняет WordStepService.save_batch():
всё в одной транзакции - если хоть одно слово не прошло проверку,
не сохраняется ни одно

Ответы:
-200 - {"ok": True}, после чего клиент перезагружает страницу
-400 - {"ok": False, "error": ...} - некорректные данные изменений или ошибка проверки слова
(в тексте ошибки указано, на каком слове она возникла)
-404 - {"ok": False, "error": ...} - задание, слово или категория не найдены
"""

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.word_steps import WordStepService


@method_decorator(
    required_type(["admin"]),
    name="dispatch"
)
class WordsBatchEndpoint(View):
    http_method_names = ["post"]
    
    def post(
            self,
            request: HttpRequest,
            task_id: int
        ) -> JsonResponse:
        
        try:
            WordStepService().save_batch(
                task_id=task_id,
                changes_json=request.POST.get("changes"),
                files=request.FILES
            )
            
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
            
        return JsonResponse({"ok": True}, status=200)
