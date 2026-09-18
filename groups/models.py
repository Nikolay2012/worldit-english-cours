from django.db import models
from users.models import Manager, Mentor, Student
from courses.models import Course, Lesson

# Create your models here.
class Schedule(models.Model):
    day_choice = (
        ('Пн', 'Понеділок'),
        ('Вт', 'Вівторок'),
        ('Ср', 'Середа'),
        ('Чт', 'Четвер'),
        ('Пт', 'П’ятниця'),
        ('Сб', 'Субота'),
        ('Нд', 'Неділя'),
    )
    day = models.CharField(max_length = 15, choices = day_choice)
    time = models.TimeField()
    adress = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    duration = models.IntegerField(default=90)

    type_choice = (("Офлайн", "Офлайн"), ("Онлайн", "Онлайн"))
    type = models.CharField(max_length = 10, choices = type_choice, default="Офлайн")

    def __str__(self):
        return f"{self.day} {self.time}, {self.type}"

class Group(models.Model):
    students = models.ManyToManyField(to = Student, related_name = "groups")
    mentor = models.ForeignKey(to = Mentor, on_delete=models.SET_NULL, blank=True, null=True, related_name = "groups")
    manager = models.ForeignKey(to = Manager, on_delete=models.SET_NULL, null=True, related_name = "groups")
    course = models.ForeignKey(to = Course, related_name = "groups", on_delete = models.SET_NULL, null = True, blank=True)
    schedules = models.ManyToManyField(Schedule, related_name = "groups", null = True)
    sub_mentor = models.ForeignKey(to = Mentor, on_delete=models.SET_NULL, blank=True, null=True, related_name = "sub_groups")
    archive_students = models.ManyToManyField(to = Student, related_name = "archive_in_groups", null=True, blank=True)
    first_lesson_date = models.DateField(blank=True, null=True)
    last_lesson_date = models.DateField(blank=True, null=True)
    count_lessons = models.IntegerField(default=80)
    is_active = models.BooleanField(default=True)
    
    type_choice = (
        ("group", "Група"),
        ("individual_mentor", "Індивідуально з ментором"),
        ("individual", "Індивідуально без ментора"),
        ("individual_task", "Індивідуально з перевіркою завдань"),
    )
    type = models.CharField(max_length = 50, choices = type_choice, default="group")
    
    def __str__(self):
        return f"<Group: {self.course.name} - {self.schedules.first()}, {self.mentor.user.full_name}>"

    def get_name(self):
        weekday = {'Пн': 1, 'Вт': 2, 'Ср': 3, 'Чт': 4, 'Пт': 5, 'Сб': 6, 'Нд': 7}
        time_str = ""
        day_str = ""
        for sch in self.schedules.all():
            time_str += sch.time.strftime('%H:%M') + "-"
            day_str += str(weekday.get(sch.day, "?"))

        mentor_id = self.mentor.identification_number if self.mentor else ""
        return f"{self.course.short_name} {time_str[:-1]} {day_str}-{mentor_id}"

    def get_count_students_text(self):
        count = self.students.count()
        if 11 <= count % 100 <= 14:
            return f"{count} учасників"
        if count % 10 == 1:
            return f"{count} учасник"
        if 2 <= count % 10 <= 4:
            return f"{count} учасники"
        return f"{count} учасників"
    
class OpenLesson(models.Model):
    lesson = models.ManyToManyField(to = Lesson, related_name = "open_lessons")
    group = models.ManyToManyField(to = Group, related_name = "open_lessons")

    def __str__(self):
        return f"<Open lesson: {self.lesson.name}, for group - {self.group}>"