"""
Модуль с маршрутами для работы клиента с сервером через fetch
"""

from django.urls import path
from english.endpoints.lesson_tasks import update_lesson_tasks_endpoint


urlpatterns = [
    path(
        "lessons/<int:lesson_id>/tasks/", 
        update_lesson_tasks_endpoint, 
        name="api_update_lesson_tasks"
    ),
]
