"""
Ядро прохождения задания

Используется эндпоинтами NextStepEndpoint (получение шага)
и StepAnswerEndpoint (ответ на шаг)

Использование:
TaskRunner(task_id, user).get_next_step(after_step_id) - следующий шаг и прогресс
TaskRunner(task_id, user).answer(step_id, data) - проверка ответа и прогресс

Ядро не знает, как устроен конкретный шаг
Сборку данных шага и проверку ответа выполняет обработчик шага,
который ядро получает из StepHandlerRegistry по виду шага (kind)

Задание ищется сразу при создании (в __init__),
только среди заданий курса английского

Логика разделена по ролям:
Персонал (admin) - без записей в БД:
-шаги идут по порядку (order): первый, или следующий после after_step_id
-ответ только проверяется, ничего не записывается
-прогресс считается по позиции шага в задании
-после обновления страницы прохождение начинается с первого шага

Студент:
-шаги задания делятся по order на выборки по 6 слов (WORDS_BATCH_SIZE)
-студент проходит выборки по очереди: следующая открывается,
когда у всех слов текущей по 6 правильных ответов (REQUIRED_CORRECT_ANSWERS)
-в выборке показывается случайное слово среди тех,
у кого правильных ответов меньше всего, кроме последнего отвеченного
-показанный, но не отвеченный шаг хранится в StudentProgress.current_step
и возвращается снова при обновлении страницы
-на один показ - один ответ: после ответа current_step обнуляется
-каждый ответ записывается в StudentAnswer,
прогресс (StudentProgress) пересчитывается после каждого ответа
-процент - правильные ответы / (шагов × 6)

Возвращаемые данные:
-.get_next_step() - {"step": данные шага или None, "progress": {"percent", "is_completed"}}
-.answer() - {"is_correct": bool, "progress": {"percent", "is_completed"}}
Если step = None - задание пройдено до конца

Из ошибок, могут подниматься:
-NotFoundError - задание или шаг не найдены в этом задании
-ValidationError - от обработчика шага (некорректный ответ), реестра (неизвестный вид шага)
или повторный ответ на уже отвеченный показ
"""

from django.db import transaction
from django.db.models import QuerySet
from django.db.models.aggregates import Count
from django.utils import timezone

from django.conf import settings
from english.models.english_task import EnglishTask
from english.models.english_task_step import EnglishTaskStep
from english.models.student_answer import StudentAnswer
from english.models.student_progress import StudentProgress
from english.services.exceptions import NotFoundError, ValidationError
from english.services.step_handlers.registry import StepHandlerRegistry
from english.services.task_runner.mixins.words import WordsTaskRunnerMixin
from users.models import CustomUser


class TaskRunner(
        WordsTaskRunnerMixin
    ):
    
    def __init__(self, task_id: int, user: CustomUser):
        
        self.user = user
        self.task = self._get_task(task_id=task_id)
        self.student = getattr(self.user, "profile_student", None)
        
        #  типы персонала (админ)
        # отдельно вынесены, по причине отличной от студента логики записи прогресса 
        # (прогресс у них отсутствует)
        self.STAFF_TYPES = ["admin"]
    
    def get_next_step(
            self, 
            after_step_id: int | None = None
        ) -> dict:
        
        if self._is_staff():
            step, progress = self._get_staff_next_step(
                after_step_id=after_step_id)
        else:
            step, progress = self._get_student_next_step()
        
        return {
            "step": self._get_step_data(step=step) if step else None,
            "progress": progress
        }
    
    def answer(self, step_id: int, data: dict) -> dict:
        
        if self._is_staff():
            return self._staff_answer(
                step_id=step_id,
                data=data
            )
        else:
            return self._student_answer(
                step_id=step_id,
                data=data
            )
    
    def _staff_answer(self, step_id: int, data: dict) -> dict:
        
        steps = self._get_steps()
        step = self._get_task_step(
            steps=steps,
            step_id=step_id
        )
        
        handler = StepHandlerRegistry().get_handler(
            kind=step.kind
        )
        
        total_steps_count = steps.count()
        completed_steps_count = steps.filter(order__lte=step.order).count()
        
        return {
            "is_correct": handler.check(step=step, data=data),
            "progress": {
                "percent": round(completed_steps_count / total_steps_count * 100),
                "is_completed": completed_steps_count == total_steps_count
            }
        }
    
    def _student_answer(self, step_id: int, data: dict) -> dict:
        
        steps = self._get_steps()
        step = self._get_task_step(
            steps=steps,
            step_id=step_id
        )
        
        handler = StepHandlerRegistry().get_handler(
            kind=step.kind
        )
        
        is_correct = handler.check(step=step, data=data)
        steps_count = steps.count()
        
        with transaction.atomic():
            try:
                progress = StudentProgress.objects.select_for_update().get(
                    student=self.student,
                    task=self.task
                )
            except StudentProgress.DoesNotExist as error:
                raise ValidationError(
                    "Цей крок вже неактуальний, оновіть сторінку"
                ) from error
            
            # Часть защиты от повторного ответа
            # То есть: если студент ответил и попытался отправить 
            # еще один запрос ответа (пока ответ обрабатывается), 
            # то сервер не обработает повторный запрос
            if progress.current_step_id != step.id:
                raise ValidationError(
                    "Цей крок вже неактуальний, оновіть сторінку"
                )
            
            answer = StudentAnswer.objects.create(
                student=self.student,
                step=step,
                is_correct=is_correct
            )
            
            handler.save_answer_details(
                answer=answer,
                step=step,
                data=data
            )
            
            self._update_progress_record(
                progress=progress,
                steps_count=steps_count
            )
        
        return {
            "is_correct": is_correct,
            "progress": self._get_student_progress(
                steps_count=steps_count,
                progress=progress
            )
        }
    
    def _update_progress_record(
        self,
        progress: StudentProgress,
        steps_count: int
    ):
        
        correct_by_step = self._get_correct_by_step()
        
        progress.answered_count = StudentAnswer.objects.filter(
            student=self.student,
            step__task=self.task
        ).count()
        
        correct_count = 0
        
        for correct in correct_by_step.values():
            correct_count += correct
        
        progress.correct_count = correct_count
        # Часть защиты от повторного ответа на вопрос, во время обработки ответа
        # То есть: студент нажал на ответ и полетел запрос на сервер,
        # кнопка то блокируется, но отправить повторный запрос можно через Network.
        # Если повторный запрос будет отправлен, то записи не произойдет потому что к этому моменту
        # progress.currect_step будет установлен как None
        progress.current_step = None
        
        # Если количество правильных ответов студента более или равно максимальному 
        # количеству правильных (steps_count * self.REQUIRED_CORRECT_ANSWER)
        # То задание считается завершенным и в записи прогресса указываются соответствующие данные
        if correct_count >= steps_count * self.REQUIRED_CORRECT_ANSWERS:
            progress.status = "completed"
            progress.completed_at = timezone.now()
            
        progress.save()
    
    def _get_staff_next_step(
            self, 
            after_step_id: int | None
        ) -> tuple:
        
        steps: QuerySet[EnglishTaskStep] = self._get_steps()
        
        if after_step_id is None:
            step = steps.first()
        else:
            after_step: EnglishTaskStep = steps.filter(pk=after_step_id).first()
            
            if after_step is None:
                raise NotFoundError(
                    "Крок не знайдено в цьому завданні"
                )
            
            step = steps.filter(order__gt=after_step.order).first()
        
        return step, self._get_staff_progress(
            steps=steps,
            step=step
        )
    
    def _get_student_next_step(self) -> tuple:
        
        next_step_methods = {
            "words": self._get_student_words_next_step,
        }
        
        method = next_step_methods.get(self.task.type)
        
        if method is None:
            raise ValidationError("Для цього типу завдання проходження не підтримується")
        
        return method()
    
    def _get_last_answered_step_id(self) -> int | None:
        
        return StudentAnswer.objects.filter(
            student=self.student,
            step__task=self.task
        ).order_by(
            "-id"
        ).values_list(
            "step_id", flat=True
        ).first()
    
    def _get_staff_progress(
            self, 
            steps: QuerySet[EnglishTaskStep], 
            step: EnglishTaskStep | None
        ) -> dict:
        
        # Если следующего шага нету, то задание пройдено
        # соответстенно 100%
        if step is None:
            return {
                "percent": 100,
                "is_completed": True
            }
        
        # В случае же, если следующий шаг есть
        # Определяем общее количестве шагов, и сколько было пройдено
        # Отталкиваясь от этого получаем процент прохождения задания
        total_steps_count = steps.count()
        completed_steps_count = steps.filter(order__lt=step.order).count()
        
        return {
            "percent": round(completed_steps_count / total_steps_count * 100),
            "is_completed": False
        }
    
    def _get_student_progress(
            self, 
            steps_count: int, 
            progress: StudentProgress
        ) -> dict:
        
        if steps_count == 0:
            return {
                "percent": 0, 
                "is_completed": False
            }
        
        return {
            "percent": round(progress.correct_count / (steps_count * self.REQUIRED_CORRECT_ANSWERS) * 100),
            "is_completed": progress.status == "completed"
        }
    
    def _get_progress_record(self) -> StudentProgress:
        
        progress, _ = StudentProgress.objects.get_or_create(
            student=self.student,
            task=self.task,
            defaults={"status": "in_progress"}
        )
        
        return progress
    
    def _get_steps(self):
        
        return self.task.steps.select_related(
            "question",
            "category" # для words progress (там прогресс по словам разделен на категории)
        ).prefetch_related(
            "question__options",
            "question__images"
        ).order_by("order")
    
    def _get_step_data(self, step: EnglishTaskStep) -> dict:
        
        handler = StepHandlerRegistry().get_handler(
            kind=step.kind
        )
        
        return handler.get_step_data(step=step)
    
    def _is_staff(self) -> bool:
        
        account_types = self.user.account_types
        
        for staff_type in self.STAFF_TYPES:
            if staff_type in account_types:
                return True
            
        return False
    
    def _get_task(self, task_id: int) -> EnglishTask:
        
        task = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID,
            is_active=True
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не знайдено")
        
        return task
    
    def _get_task_step(
            self, 
            steps: QuerySet[EnglishTaskStep], 
            step_id: int
        ) -> EnglishTaskStep:
        
        step = steps.filter(pk=step_id).first()
        
        if step is None:
            raise NotFoundError("Крок не знайдено в цьому завданні")
        
        return step
    
    def _get_correct_by_step(self) -> dict[int, int]:
        
        # Получаем и сразу группируем правильные ответы студента в задании
        return dict(
            StudentAnswer.objects.filter(
                student=self.student,
                step__task=self.task,
                is_correct=True
            # Указываем, по какому полю будем группировать
            ).values(
                "step_id"
            # Для каждой группы считаем количество правильных ответов
            # Например: Шаг 12 - 3 правильных ответа. 
            # После values_list это будет запиано так: ((12, 3), (..., ...), (..., ...), ...)
            ).annotate(
                correct=Count("id")
            # Возвращаем результат кортежеами, без лишних полей
            ).values_list(
                "step_id", "correct"
            )
        )
