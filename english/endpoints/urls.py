"""
Модуль с маршрутами для работы клиента с сервером через fetch
"""

from django.urls import path
from english.endpoints.lesson_tasks import LessonTasksEndpoint


urlpatterns = [
    path(
        "lessons/<int:lesson_id>/tasks/", 
        LessonTasksEndpoint.as_view(), 
        name="api_update_lesson_tasks"
    ),
]
