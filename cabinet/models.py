from django.db import models
from groups.models import Group

# Create your models here.

class Event(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()

    def __str__(self):
        return f"<Event: {self.title}, {self.date}>"
    
class CalendarEvent(models.Model):
    type_choices = (
        ('Змінена дата', "Змінена дата"),
        ('Скасовано/Пенесено', 'Скасовано/Пенесено'),
        ('Канікули', "Канікули"),
    )
    group = models.ManyToManyField(Group)
    type = models.CharField(max_length=255, choices=type_choices)
    start_date = models.DateField()
    finish_date = models.DateField(default=None, null=True)
    time = models.TimeField(default=None, null=True)

    def __str__(self):
        return f"<Calendar event: {self.type}, {self.start_date}, in group {self.group.name}>"