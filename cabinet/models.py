from django.db import models
from groups.models import Group
from users.models import CustomUser

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
    groups = models.ManyToManyField(Group, related_name="calendar_events")
    type = models.CharField(max_length=255, choices=type_choices)
    start_date = models.DateField()
    finish_date = models.DateField(default=None, null=True, blank=True)
    time = models.TimeField(default=None, null=True, blank=True)

    def __str__(self):
        return f"<Calendar event: {self.type}, {self.start_date}, in {self.groups.count()} groups>"
    
class StaffTask(models.Model):
    creator = models.ForeignKey(to=CustomUser, related_name="created_tasks", on_delete=models.SET_NULL, null=True)
    executor = models.ForeignKey(to=CustomUser, related_name="my_tasks", on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    finish_date = models.DateField()
    title = models.CharField(max_length=120)
    description = models.TextField()
    git_hub_url = models.URLField(blank=True, null=True)
    status_choices = (
        ("new", "Нова задача"),
        ("in_progress", "В роботі"),
        ("check", "Перевірка"),
        ("complete", "Готово")
    )
    status = models.CharField(max_length=15, choices=status_choices)
    priority_choices = (
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("lowest", "Lowest")
    )
    priority = models.CharField(max_length=10, choices=priority_choices)
    def __str__(self):
        return f"<Task for {self.executor.full_name} until {self.finish_date}>"
    
class TaskFile(models.Model):
    task = models.ForeignKey(to=StaffTask, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="cabinet/staff_tasks/")
    type_choices = (
        ("creator", "creator"),
        ("executor", "executor")
    )
    type = models.CharField(max_length=12, choices=type_choices)
    def __str__(self):
        return f"<File to task {self.task.id} from {self.type}>"
