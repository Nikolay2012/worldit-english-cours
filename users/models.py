from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    gender_choices = (
        ('Чоловічий', "Чоловічий"),
        ('Жіночий', 'Жіночий'),
    )
    phone_number = models.CharField(max_length=15, unique=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=60, default=None, null=True)
    gender = models.CharField(max_length=10, default=None, null=True, choices=gender_choices)

    def __str__(self):
        return f"<User: {self.last_name} {self.first_name}>"
    
class Mentor(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"<Mentor: {self.user.last_name} {self.user.first_name}>"
    
class Manager(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"<Manager: {self.user.last_name} {self.user.first_name}>"
    
class Parent(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE)
    telegram_username = models.CharField(max_length=32, default=None, null=True)
    type = models.CharField(max_length=32, default="Мати")
    
    def __str__(self):
        student_str = ""
        student_list = self.students
        for stud in student_list:
            student_str += stud.user.first_name
        return f"<Parent: {self.user.last_name} {self.user.first_name}, {self.type} для {student_str[:-1]}>"
    

class Student(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE)
    parents = models.ManyToManyField(Parent, related_name="students")
    
    def __str__(self):
        return f"<Student: {self.user.last_name} {self.user.first_name}>"