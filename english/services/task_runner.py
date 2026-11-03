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

import random

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
from users.models import CustomUser


class TaskRunner:
    def __init__(self, task_id: int, user: CustomUser):
        
        self.user = user
        self.task = self._get_task(task_id=task_id)
        self.student = getattr(self.user, "profile_student", None)
        
        #  типы персонала (админ)
        # отдельно вынесены, по причине отличной от студента логики записи прогресса 
        # (прогресс у них отсутствует)
        self.STAFF_TYPES = ["admin"]
        
        # Количество правильных ответов, которое должно быть дано по слову, 
        # для того чтобы сервер оценил его как пройденное верно
        self.REQUIRED_CORRECT_ANSWERS = 6
        
        # Партия слов (6 штук), которые будут отображены студенту до тех пор, 
        # пока он корректно не ответит на все вопросы по этим словам
        self.WORDS_BATCH_SIZE = 6
        
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
        
        steps = list(self._get_steps())
        progress = self._get_progress_record()
        
        # Если студент перешел на новый вопрос, 
        # но после этого заркыл страницу и перезашел на нее, 
        # или просто обновил страницу
        # При следующем запросе сервер увидит, что слово было показано, 
        # но не отвечено, и возвращает его же
        if progress.current_step_id is not None:
            for step in steps:
                if step.id == progress.current_step_id:
                    return step, self._get_student_progress(
                        steps_count=len(steps),
                        progress=progress
                    )
        
        correct_by_step = self._get_correct_by_step()
        batch = self._get_current_batch(
            steps=steps,
            correct_by_step=correct_by_step
        )
        
        if not batch:
            return None, self._get_student_progress(
                steps_count=len(steps),
                progress=progress
            )
        
        candidates = self._get_candidates(
            batch=batch,
            correct_by_step=correct_by_step,
            last_step_id=self._get_last_answered_step_id()
        )
        
        # Выбираем случайный шаг из уже подготовленных кандидатов 
        # (отбираются те шаги, в которых наименьшее количество правильных ответов)
        step = random.choice(candidates)
        
        progress.current_step = step
        progress.save()
        
        return step, self._get_student_progress(
            steps_count=len(steps),
            progress=progress
        )
    
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
    
    def _get_current_batch(
        self,
        steps: list[EnglishTaskStep],
        correct_by_step: dict[int, int]
    ) -> list[EnglishTaskStep]:
        
        # Перебираем общий набор вопросов с шагом в 6 (self.WORDS_BATCH_SIZE = 6)
        for start in range(0, len(steps), self.WORDS_BATCH_SIZE):
            # Проводим срез шагов, с индекса start по инекс start + self.WORDS_BATCH_SIZE
            # Таким образом, формируем выборку из 6 
            # Если в выборке число, которое не делится нацело на 6 (например: 20),
            # до Python обрежет конец до длины списка, как это и всегда и работает в Python
            batch = steps[start:start + self.WORDS_BATCH_SIZE]
            
            for step in batch:
                step: EnglishTaskStep
                
                if correct_by_step.get(step.id, 0) < self.REQUIRED_CORRECT_ANSWERS:
                    return batch
        
        return []
    
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
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
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
    
    def _get_candidates(
        self,
        batch: list[EnglishTaskStep],
        correct_by_step: dict[int, int],
        last_step_id: int | None
    ) -> list[EnglishTaskStep]:
        
        candidates = []
        
        # Наименьшее число правильных ответов среди незавершенных шагов задания
        # None - пока не встретили ни одного не завершенного шага
        minimum_correct = None
        
        # Перебираем каждый шаг в выборке
        # Важно то, что шаги не создаются в процессе (новые шаги)
        # Работа ведется с теми шагами, которые были и созданы при парсинге csv
        # Тут же происходит лишь отбор уже существующих шагов, по критериям
        for step in batch:
            # Получаем количество правильных ответов
            correct = correct_by_step.get(step.id, 0)
            
            # Шаг уже набрал 6 правильных ответов, а значит - завершнен
            if correct >= self.REQUIRED_CORRECT_ANSWERS:
                continue
            
            # Нашли шаг с наименьшим количество правильных ответов, чем у всех до него
            # Прошлые кандидаты больше не подходят, начинаем список заново - с этого шага
            if minimum_correct is None or correct < minimum_correct:
                minimum_correct = correct
                
                candidates = [step]
            
            # Количество правильных ответов такое же, сколько и у всех других кандидатов списка
            # По этому добавляем этот шаг в кандидаты
            elif correct == minimum_correct:
                candidates.append(step)
        
        # Если выбор есть - убираем последний показанный шаг
        # То есть, если в candidates попал такой же шаг, 
        # какой и был до этого - мы его не добавляем (!=)
        # Делаем это потому, что без без этого возможно было бы попадание одного и того же шага дважды
        if len(candidates) > 1:
            candidates = [step for step in candidates if step.id != last_step_id]
        
        return candidates
    
    def get_words_progress(self):
        
        steps = list(self._get_steps())
        
        # У персонала (админ и модератор) нету сохраненного в БД прогресса
        if self._is_staff():
            correct_by_step = {}
        else:
            correct_by_step = self._get_correct_by_step()
        
        registry = StepHandlerRegistry()
        categories = {}
        
        for step in steps:
            item = registry.get_handler(
                kind=step.kind
            ).get_list_item(step=step)
            
            item["correct_count"] = min(
                correct_by_step.get(step.id, 0),
                self.REQUIRED_CORRECT_ANSWERS
            )
            
            category_name = step.category.name if step.category else ""
            
            if category_name not in categories:
                categories[category_name] = []
            
            categories[category_name].append(item)
        
        result = []
        
        for category_name, words in categories.items():
            result.append({
                "category": category_name,
                "words": words
            })
        
        return {
            "required_correct_answers": self.REQUIRED_CORRECT_ANSWERS,
            "categories": result
        }
