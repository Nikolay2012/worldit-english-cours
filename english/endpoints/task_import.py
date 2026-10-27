"""
Эндпоинт импорта задания из csv файла

Используется на странице пустого задания:
админ или ментор выбирает csv файл в модалке «Завантаження списку слів»,
и по кнопке «Продовжити» файл отправляется сюда

Маршрут:
POST /courses/english/api/tasks/<task_id>/import/

Доступ - только админ или ментор (required_type(["admin", "mentor"]))

В запросе (multipart/form-data) передаётся:
-file - csv файл в кодировке UTF-8, не больше 1 МБ

Ответы:
-200 {"ok": true, "data": [...]} - задание создано, в data список слов по категориям
-400 {"ok": false, "error": "..."} - нет файла, не .csv, неверный размер или ошибка в рядках файла
-404 {"ok": false, "error": "..."} - задание не найдено или не из курса английского
-409 {"ok": false, "error": "..."} - у задания уже есть шаги, импорт возможен только в пустое задание

Парсинг файла и запись в БД делает импортёр (english/services/task_importers)
Эндпоинт только проверяет, что файл передан,
и переводит ошибки импортёра в HTTP-ответы
"""

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.task_importers.word import WordImporter
from english.services.exceptions import NotFoundError, ConflictError, ValidationError


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
        
        uploaded_file = request.FILES.get("file")
        
        if uploaded_file is None:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Файл не передано"
                }, 
                status=400
            )
        
        try:
            words_list = WordImporter().import_file(
                task_id=task_id,
                file=uploaded_file
            )
        except NotFoundError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=404
            )
        
        except ConflictError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=409
            )
        
        except ValidationError as error:
            return JsonResponse(
                {"ok": False, "error": error.message}, 
                status=400
            )
        
        print(words_list)
        
        return JsonResponse(
            {"ok": True, "data": words_list}, 
            status=200
        )
