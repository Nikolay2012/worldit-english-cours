from django.db import models
from django.templatetags.static import static
from django.urls import reverse


class EnglishTask(models.Model):
    
    block_choices = (
        ("lesson", "Основний урок"),
        ("homework", "Домашня практика")
    )
    
    type_choices = (
        ("words", "Слова"),
        ("sentences", "Речення"),
        ("video", "Відео"),
        ("reading", "Читання"),
    )
    
    icon_choices = (
        ("history", "Історія"),
        ("text", "Текст"),
        ("test", "Тест"),
        ("theory", "Теорія"),
        ("film", "Фільм"),
        ("audio", "Аудіо"),
    )
    
    name = models.CharField(max_length=255)
    block = models.CharField(max_length=20, choices=block_choices)
    type = models.CharField(max_length=20, choices=type_choices)
    icon = models.CharField(max_length=20, choices=icon_choices)
    
    order = models.IntegerField()
    is_available = models.BooleanField(default=True)
    
    lesson = models.ForeignKey(
        "courses.Lesson",
        related_name="english_tasks",
        on_delete=models.SET_NULL,
        null=True,
    )
    
    @property
    def icon_url(self):
        return static(f"english/img/icons/tasks/icons/{self.icon}.svg")
    
    def __str__(self):
        return f"<EnglishTask: {self.order}. {self.name}>"
    
    def get_absolute_url(self):
        return reverse(
            "english:english_task", 
            kwargs={
                "module_id": self.lesson.module_id,
                "lesson_id": self.lesson_id,
                "pk": self.pk
            }
        )
    
    class Meta:
        constraints = [
            # Порядок завдання має бути унікальним в одному блоці
            # Під блоками маються на увазі блоки «основний урок» або «дз»
            models.UniqueConstraint(
                fields=["lesson", "block", "order"],
                name="unique_english_task_order_in_block"
            )
        ]
