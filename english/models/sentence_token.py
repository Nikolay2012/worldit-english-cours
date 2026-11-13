from django.db import models


class SentenceToken(models.Model):
    
    sentence = models.ForeignKey(
        "english.Sentence",
        on_delete=models.CASCADE,
        related_name="tokens"
    )
    text = models.CharField(max_length=50)
    order = models.IntegerField()
    is_lowercase = models.BooleanField(default=False)
    
    def __str__(self):
        return f"<SentenceToken: {self.sentence} - {self.text}>"
    
    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["sentence", "order"],
                name="unique_sentence_token_order"
            )
        ]
