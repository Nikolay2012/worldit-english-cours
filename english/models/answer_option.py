from django.db import models


class AnswerOption(models.Model):
    
    question = models.ForeignKey(
        "english.Question",
        related_name="options",
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField()
    
    def __str__(self):
        return f"<AnswerOption: {self.question} - відповідь «{self.text}»>"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"],
                name="unique_answer_option_order_in_question"
            ),
            # Кожен варіант відповіді на питання має бути унікальник
            models.UniqueConstraint(
                fields=["question", "text"],
                name="unique_answer_option_text_in_question"
            )
        ]
