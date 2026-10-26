from django.db import models
from django.core.validators import FileExtensionValidator


class Video(models.Model):
    
    task = models.OneToOneField(
        "english.EnglishTask",
        related_name="video",
        on_delete=models.CASCADE
    )
    
    file = models.FileField(
        upload_to="english/videos/",
        validators=[
            # пока что только эти форматы
            FileExtensionValidator(allowed_extensions=["mp4", "webm"])
        ]
    )
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    preview = models.ImageField(
        upload_to="english/videos/previews/",
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"<Video: {self.task} - {self.title}>"
