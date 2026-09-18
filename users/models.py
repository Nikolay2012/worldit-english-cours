from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    gender_choices = (
        ('Чоловічий', "Чоловічий"),
        ('Жіночий', 'Жіночий'),
    )
    phone_number = models.CharField(max_length=25, unique=True, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=60, default=None, null=True, blank=True)
    gender = models.CharField(max_length=10, default=None, null=True, choices=gender_choices)
    first_name_en = models.CharField(max_length=50, blank=True, null=True)
    last_name_en = models.CharField(max_length=50, blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    messenger = models.CharField(max_length=255, blank=True, null= True)
    avatar = models.ImageField(upload_to="users/avatars", blank=True, null=True)
    visible_password = models.CharField(max_length=100, default=None, blank=True, null=True)

    def __str__(self):
        return f"<User: {self.full_name}>"
    
    @property
    def account_types(self):
        returned_types = []
        if self.is_superuser: 
            returned_types.append("admin")
        type_list = ["mentor", "manager", "parent", "student"]
        for type in type_list:
            if hasattr(self, f"profile_{type}"):
                returned_types.append(type)
        return returned_types
    
    @property
    def full_name(self):
        if self.last_name and self.first_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username
        
    def get_groups(self):
        groups = []
        for type in ["mentor", "manager", "student"]:
            if hasattr(self, f"profile_{type}"):
                groups.extend(getattr(self, f"profile_{type}").groups.all())
        if hasattr(self, "profile_parent"):
            for student in self.profile_parent.students.all():
                for group in student.groups.all():
                    group.student_id_for_parent = student.id
                    groups.append(group)
        return groups
            
class Mentor(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE, related_name="profile_mentor")
    identification_number = models.IntegerField(default=0)

    def __str__(self):
        return f"<Mentor: {self.user.full_name}>"
    
class Manager(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE, related_name="profile_manager")
    
    def __str__(self):
        return f"<Manager: {self.user.full_name}>"
    
class Parent(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE, related_name="profile_parent")
    type = models.CharField(max_length=32, default="Мати")
    
    def __str__(self):
        student_str = ""
        student_list = self.students.all()
        for stud in student_list:
            student_str += stud.user.full_name
            student_str += ", "
        return f"<Parent: {self.user.full_name}, {self.type} для [{student_str[:-2]}]>"
    

class Student(models.Model):
    user = models.OneToOneField(to = CustomUser, on_delete=models.CASCADE, related_name="profile_student")
    parents = models.ManyToManyField(Parent, related_name="students", blank=True, null=True)
    can_pay = models.BooleanField(default=False)
    is_club_member = models.BooleanField(default=False)
    hobbies = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"<Student: {self.user.full_name}>"