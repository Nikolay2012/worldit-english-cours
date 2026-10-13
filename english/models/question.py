from django.db import models


class Question(models.Model):
    
    step = models.OneToOneField(
        "english.EnglishTaskStep",
        on_delete=models.CASCADE,
        related_name="question"
    )
    text = models.CharField(max_length=255, blank=True)
    image = models.ImageField(
        upload_to="courses/english/questions/",
        blank=True
    )
    allows_multiple = models.BooleanField(default=False)
    
    def __str__(self):
        return f"<Question: {self.step.order}>"
