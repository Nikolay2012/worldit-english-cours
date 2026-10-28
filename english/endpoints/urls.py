"""
Модуль с маршрутами для работы клиента с сервером через fetch
"""

from django.urls import path
from english.endpoints.lesson_tasks import LessonTasksEndpoint
from english.endpoints.task_import import TaskImportEndpoint
from english.endpoints.task_steps import TaskStepsEndpoint
from english.endpoints.create_word import CreateWordEndpoint

app_name = "api"

urlpatterns = [
    path(
        "lessons/<int:lesson_id>/tasks/", 
        LessonTasksEndpoint.as_view(), 
        name="api_update_lesson_tasks"
    ),
    path(
        "tasks/<int:task_id>/import/", 
        TaskImportEndpoint.as_view(), 
        name="api_import_task_data"
    ),
    path(
        "tasks/<int:task_id>/steps/", 
        TaskStepsEndpoint.as_view(), 
        name="api_delete_task_steps"
    ),
    path(
        "tasks/<int:task_id>/word/", 
        CreateWordEndpoint.as_view(), 
        name="api_create_word"
    ),
]
