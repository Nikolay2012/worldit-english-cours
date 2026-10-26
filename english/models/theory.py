from django.db import models


class Theory(models.Model):

    task = models.ForeignKey(
        "english.EnglishTask",
        related_name="theories",
        on_delete=models.CASCADE
    )
    
    title = models.CharField(max_length=255)
    text = models.TextField()
    order = models.IntegerField()
    image = models.ImageField(
        upload_to="english/theory/",
        blank=True
    )
    
    def __str__(self):
        return f"<Theory: {self.title}>"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "order"],
                name="unique_english_theory_order_in_task"
            )
        ]
