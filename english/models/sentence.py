from django.db import models


class Sentence(models.Model):
    
    step = models.OneToOneField(
        "english.EnglishTaskStep",
        on_delete=models.CASCADE,
        related_name="sentence"
    )
    prompt = models.TextField()
    answer = models.TextField()
    template = models.TextField(blank=True, default="")
    
    @property
    def is_fill(self):
        return True if self.template else False
    
    def __str__(self):
        return f"<Sentence: {self.prompt}>"
