"""
Модуль с маршрутами для работы клиента с сервером через fetch
"""

from django.urls import path
from english.endpoints.lesson_tasks import LessonTasksEndpoint
from english.endpoints.next_step import NextStepEndpoint
from english.endpoints.sentence import SentenceEndpoint
from english.endpoints.sentence_batch import SentencesBatchEndpoint
from english.endpoints.sentences_progress import SentencesProgressEndpoint
from english.endpoints.step_answer import StepAnswerEndpoint
from english.endpoints.task_import import TaskImportEndpoint
from english.endpoints.task_steps import TaskStepsEndpoint
from english.endpoints.word import WordEndpoint
from english.endpoints.words_batch import WordsBatchEndpoint
from english.endpoints.words_progress import WordsProgressEndpoint
from english.endpoints.sentence_preview import SentencePreviewEndpoint

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
        "tasks/<int:task_id>/words/", 
        WordEndpoint.as_view(), 
        name="api_create_word"
    ),
    path(
        "tasks/<int:task_id>/words/<int:step_id>/", 
        WordEndpoint.as_view(), 
        name="api_update_word"
    ),
    
    path(
        "tasks/<int:task_id>/next-step/", 
        NextStepEndpoint.as_view(), 
        name="api_next_step"
    ),
    path(
        "tasks/<int:task_id>/steps/<int:step_id>/answer/", 
        StepAnswerEndpoint.as_view(), 
        name="api_step_answer"
    ),
    path(
        "tasks/<int:task_id>/words-progress/", 
        WordsProgressEndpoint.as_view(), 
        name="api_words_progress"
    ),
    path(
        "tasks/<int:task_id>/words/batch/", 
        WordsBatchEndpoint.as_view(), 
        name="api_words_batch"
    ),
    path(
        "tasks/<int:task_id>/sentences/", 
        SentenceEndpoint.as_view(), 
        name="api_create_sentence"
    ),
    path(
        "tasks/<int:task_id>/sentences/<int:step_id>/", 
        SentenceEndpoint.as_view(), 
        name="api_update_sentence"
    ),
    path(
        "tasks/<int:task_id>/sentences/preview/", 
        SentencePreviewEndpoint.as_view(), 
        name="api_preview_sentence"
    ),
    path(
        "tasks/<int:task_id>/sentences-progress/",
        SentencesProgressEndpoint.as_view(),
        name="api_sentences_progress"
    ),
    path(
        "tasks/<int:task_id>/sentences/batch/",
        SentencesBatchEndpoint.as_view(),
        name="api_sentences_batch"
    )
]
