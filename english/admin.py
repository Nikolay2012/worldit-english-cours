from django.contrib import admin
from english.models import *

# Register your models here.
admin.site.register([
    AnswerOption,
    EnglishTaskStep,
    EnglishTask,
    OpenEnglishTask,
    Question,
    ReadingText,
    SentenceWord,
    Sentence,
    StudentAnswer,
    StudentProgress,
    Theory,
    Video,
    WordCategory,
    QuestionImage
])