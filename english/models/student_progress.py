from django.db import models


class StudentProgress(models.Model):
    
    status_choices = (
        ("completed", "Виконано"),
        ("in_progress", "Виконується")
    )
    
    student = models.ForeignKey(
        "users.Student",
        related_name="english_task_progress",
        on_delete=models.CASCADE
    )
    
    current_step = models.ForeignKey(
        "english.EnglishTaskStep",
        related_name="progress",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    
    answered_count = models.IntegerField()
    correct_count = models.IntegerField()
    task = models.ForeignKey(
        "english.EnglishTask",
        related_name="progress",
        on_delete=models.CASCADE
    )
    
    status = models.CharField(max_length=20, choices=status_choices)
    started_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"<StudentProgress: {self.student.user.full_name} - {self.task} - {self.current_step}>"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                # В одного студента може бути лише один запис прогресу по певному завданню
                fields=["student", "task"],
                name="unique_student_english_task_progress"
            )
        ]
