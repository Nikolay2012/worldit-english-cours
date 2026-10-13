from django.db import models


class Sentence(models.Model):
    
    step = models.OneToOneField(
        "english.EnglishTaskStep",
        on_delete=models.CASCADE,
        related_name="sentence"
    )
    prompt = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
    template = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"<Sentence: {self.prompt}>"
