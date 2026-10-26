from django.db import models


class QuestionImage(models.Model):
    
    image = models.ImageField(
        upload_to="english/questions/",
        null=True,
        blank=True
    )
    
    source_url = models.CharField(max_length=500, blank=True)
    
    order = models.IntegerField()
    
    is_placeholder = models.BooleanField(default=False)
    
    question = models.ForeignKey(
        "english.Question",
        on_delete=models.CASCADE,
        related_name="images"
    )
    
    def __str__(self):
        return f"<QuestionImage: {self.question} - {self.order}>"
    
    class Meta:
        constraints = [
            # Порядок зображення має бути унікальним в одному питанні
            models.UniqueConstraint(
                fields=["question", "order"],
                name="unique_english_question_image_order_question"
            )
        ]
