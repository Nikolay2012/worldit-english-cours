from django.urls import path, include
from django.views.generic import RedirectView
from english.views import AllModulesView, EnglishTaskView, ModuleView

# Для редиректа на страницу modules/
app_name = "english"

urlpatterns = [
    path(
        "", 
        RedirectView.as_view(
            pattern_name="english:all_english_modules", 
            permanent=False
        )
    ),
    path("modules/", AllModulesView.as_view(), name="all_english_modules"),
    path("modules/<int:pk>/", ModuleView.as_view(), name="english_module"),
    path(
        "modules/<int:module_id>/lessons/<int:lesson_id>/tasks/<int:pk>/",
        EnglishTaskView.as_view(),
        name="english_task"
    ),
    path("api/", include("english.endpoints.urls")),
]
