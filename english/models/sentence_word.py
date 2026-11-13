from django.db import models


class SentenceWord(models.Model):
    
    sentence = models.ForeignKey(
        "english.Sentence",
        on_delete=models.CASCADE,
        related_name="words"
    )
    text = models.CharField(max_length=50)
    order = models.IntegerField()
    is_lowercase = models.BooleanField(default=False)
    
    def __str__(self):
        return f"<SentenceWord: {self.sentence} - {self.text}>"
    
    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["sentence", "order"],
                name="unique_sentence_word_order"
            )
        ]
