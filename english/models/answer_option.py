from django.db import models


class AnswerOption(models.Model):
    
    language_choices = (
        ("en", "Англійська"),
        ("uk", "Українська")
    )
    
    question = models.ForeignKey(
        "english.Question",
        related_name="options",
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    language = models.CharField(
        max_length=2, 
        choices=language_choices,
        default="uk"
    )
    order = models.IntegerField()
    
    def __str__(self):
        return f"<AnswerOption: {self.question} - відповідь «{self.text}»>"
    
    class Meta:
        constraints = [
            # Порядок кожного варіанту відповіді має бути унікальним для питання (враховуючи мову відповіді)
            models.UniqueConstraint(
                fields=["question", "language", "order"],
                name="unique_answer_option_order_in_question"
            ),
            # Кожен варіант відповіді на питання має бути унікальними (враховуючи мову відповіді)
            models.UniqueConstraint(
                fields=["question", "language", "text"],
                name="unique_answer_option_text_in_question"
            )
        ]
