from django.db import models

class SentenceWordVariant(models.Model):
    
    task = models.ForeignKey(
        "english.EnglishTask",
        on_delete=models.CASCADE,
        related_name="word_variants"
    )
    text = models.CharField(max_length=50)
    row = models.IntegerField()
    position = models.IntegerField()
    normalized = models.CharField(max_length=50)
    
    def __str__(self):
        return super().__str__()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "row", "position"],
                name="unique_sentence_word_variant_cell"
            )
        ]
