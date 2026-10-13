from django.db import models


class EnglishTaskStep(models.Model):
    
    # Вариант уроку
    kind_choices = (
        ("question", "Питання"),
        ("sentence", "Речення"),
    )
    
    task = models.ForeignKey(
        "english.EnglishTask",
        related_name="steps",
        on_delete=models.CASCADE
    )
    
    kind = models.CharField(max_length=20, choices=kind_choices)
    
    order = models.IntegerField()
    
    category = models.ForeignKey(
        "english.WordCategory",
        related_name="steps",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        constraints = [
            # уникальній для задания
            models.UniqueConstraint(
                fields=["task", "order"],
                name="unique_english_task_step_order_in_task"
            )
        ]
    
    def __str__(self):
        return f"<EnglishTaskStep: {self.task} - крок {self.order}>"
