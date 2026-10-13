from django.db import models


class SentenceWord(models.Model):
    
    sentence = models.ForeignKey(
        "english.Sentence",
        on_delete=models.CASCADE,
        related_name="words"
    )
    text = models.CharField(max_length=50)
    
    def __str__(self):
        return f"<SentenceWord: {self.sentence} - {self.text}>"
