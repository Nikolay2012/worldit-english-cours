"""
Эндпоинт создания и редактирования слова в задании типа "Слова"

Используется в модалке списка слов:
-«Додати слова» в категории - создание нового слова
-клик по строке слова - редактирование этого слова
По кнопке «Зберегти» клиент отправляет сюда данные формы

Маршруты:
POST /courses/english/api/tasks/<task_id>/words/ - создание
POST /courses/english/api/tasks/<task_id>/words/<step_id>/ - редактирование

Оба действия идут через POST, а не PUT,
потому что Django разбирает файлы (request.FILES) только для POST
Есть step_id в адресе - редактирование, нет - создание

Доступ - только админ или ментор (required_type(["admin", "mentor"]))

В запросе (multipart/form-data) передаётся:
-word - слово
-translation - перевод
-category - категория слова (только при создании)
-image_0, image_1 - новые картинки, если их выбрали
-remove_image_0, remove_image_1 = "1" - если картинку удалили (только при редактировании)

Ответы:
-200 {"ok": true, "data": [...]} - слово сохранено, в data полный список слов по категориям
-400 {"ok": false, "error": "..."} - пустое слово или перевод, неверная картинка, повторяющийся перевод
-404 {"ok": false, "error": "..."} - задание, слово или категория не найдены

Вся работа с данными находится в WordStepService
Эндпоинт только выбирает метод сервиса
и переводит его ошибки в HTTP-ответы
"""

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from WorldIT.decorators import required_type
from english.services.exceptions import NotFoundError, ValidationError
from english.services.word_steps import WordStepService


@method_decorator(
    required_type(['admin', 'mentor']), 
    name="dispatch"
)
class WordEndpoint(View):
    
    def post(
        self,
        request: HttpRequest,
        task_id: int,
        step_id: int | None = None
    ) -> JsonResponse:
    
        service = WordStepService()
        
        try:
            if step_id is None:
                words_list = service.create(
                    task_id=task_id,
                    data=request.POST,
                    files=request.FILES
                )
            else:
                words_list = service.update(
                    task_id=task_id,
                    step_id=step_id,
                    data=request.POST,
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
        
        return JsonResponse(
            {"ok": True, "data": words_list},
            status=200
        )
