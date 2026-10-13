from django.db import models


class StudentAnswer(models.Model):
    
    student = models.ForeignKey(
        "users.Student",
        related_name="english_answers",
        on_delete=models.CASCADE
    )
    
    step = models.ForeignKey(
        "english.EnglishTaskStep",
        related_name="answers",
        # пока остаются записи student answer, не удаляем их
        # в противном случае ответы студента будут, 
        # без конкретного задания на которые были даны
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    
    is_correct = models.BooleanField(default=False)
    selected_options = models.ManyToManyField(
        "english.AnswerOption",
        related_name="answers",
        blank=True
    )
    
    built_sentence = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"<StudentAnswer: {self.student} - {self.step}>"
