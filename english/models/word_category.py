from django.db import models


class WordCategory(models.Model):
    
    name = models.CharField(max_length=255, unique=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"<WordCategory: {self.name}>"
