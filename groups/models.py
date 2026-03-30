from django.db import models
from users.models import Manager, Mentor, Student
from courses.models import Course, Lesson

# Create your models here.
class Schedule(models.Model):
    day_choice = (
        ('Понеділок', 'Понеділок'),
        ('Вівторок', 'Вівторок'),
        ('Середа', 'Середа'),
        ('Четвер', 'Четвер'),
        ('П’ятниця', 'П’ятниця'),
        ('Субота', 'Субота'),
        ('Неділя', 'Неділя'),
    )
    day = models.CharField(max_length = 15, choices = day_choice)
    time = models.TimeField()

    def __str__(self):
        return f"{self.day} {self.time}"

class Group(models.Model):
    students = models.ManyToManyField(to = Student, related_name = "groups")
    mentor = models.ForeignKey(to = Mentor, on_delete=models.SET_NULL, blank=True, null=True, related_name = "groups")
    manager = models.ForeignKey(to = Manager, on_delete=models.SET_NULL, null=True, related_name = "groups")
    course = models.ForeignKey(to = Course, related_name = "groups", on_delete = models.SET_NULL, null = True)
    schedules = models.ManyToManyField(Schedule, related_name = "groups", null = True)
    sub_mentor = models.ForeignKey(to = Mentor, on_delete=models.SET_NULL, blank=True, null=True, related_name = "sub_groups")
    
    type_choice = (
        ("group", "Група"),
        ("individual_mentor", "Індивідуально з ментором"),
        ("individual", "Індивідуально без ментора"),
        ("individual_task", "Індивідуально з перевіркою завдань"),
    )
    type = models.CharField(max_length = 50, choices = type_choice, default="group")
    
    def __str__(self):
        return f"<Group: {self.course.name} - {self.schedules.first()}, {self.mentor.user.full_name}>"
    
class OpenLesson(models.Model):
    lesson = models.ManyToManyField(to = Lesson, related_name = "open_lessons")
    group = models.ManyToManyField(to = Group, related_name = "open_lessons")

    def __str__(self):
        return f"<Open lesson: {self.lesson.name}, for group - {self.group}>"