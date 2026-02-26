from django.db import models

# Create your models here.
class CourseStatus(models.Model):
    name = models.CharField(max_length = 50)
    color = models.CharField(max_length = 50)
    def __str__(self):
        return f"<Status: {self.name}>"

class Course(models.Model):
    name = models.CharField(max_length = 255)
    description = models.TextField()
    short_description = models.CharField(max_length=255)
    range_age = models.CharField(max_length=5, default="9-17")
    image = models.ImageField(upload_to="courses/")
    status = models.ForeignKey(to = CourseStatus, related_name = "courses", on_delete = models.SET_NULL, null = True)

    def __str__(self):
        return f"<Course: {self.name}>"
    
class Module(models.Model):
    name = models.CharField(max_length = 255)
    course = models.ForeignKey(to = Course, related_name = "modules", on_delete = models.CASCADE)

    def __str__(self):
        return f"<Module: {self.name}, course - {self.course.name}>"
    
class Lesson(models.Model):
    name = models.CharField(max_length = 255)
    module = models.ForeignKey(to = Course, related_name = "lessons", on_delete = models.CASCADE)

    def __str__(self):
        return f"<Lesson: {self.name}, course - {self.module.course.name}>"