from django.db import models


class ReadingText(models.Model):
    
    task = models.OneToOneField(
        "english.EnglishTask",
        related_name="reading_text",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255, blank=True)
    
    # Чистый html с тегами форматирования
    text = models.TextField()
    
    def __str__(self):
        return f"<ReadingText: {self.task} - {self.title}>"
