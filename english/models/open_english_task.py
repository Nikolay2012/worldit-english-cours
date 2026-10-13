from django.db import models


class OpenEnglishTask(models.Model):
    
    student = models.ForeignKey(
        "users.Student",
        related_name="open_english_tasks",
        on_delete=models.CASCADE
    )
    
    task = models.ForeignKey(
        "english.EnglishTask",
        related_name="open_english_tasks",
        on_delete=models.CASCADE
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "student"],
                name="unique_open_english_task_student"
            )
        ]
    
    def __str__(self):
        return f"<OpenEnglishTask: {self.student.user.full_name} - {self.task}>"
