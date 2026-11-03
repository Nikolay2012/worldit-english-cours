
import random

from english.models.english_task_step import EnglishTaskStep
from english.services.step_handlers.registry import StepHandlerRegistry
from english.services.task_runner.mixins.base import TaskRunnerBase


class WordsTaskRunnerMixin(TaskRunnerBase):
    
    # Количество правильных ответов, которое должно быть дано по слову, 
    # для того чтобы сервер оценил его как пройденное верно
    REQUIRED_CORRECT_ANSWERS = 6
    
    # Партия слов (6 штук), которые будут отображены студенту до тех пор, 
    # пока он корректно не ответит на все вопросы по этим словам
    WORDS_BATCH_SIZE = 6
    
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
    
    def _get_student_words_next_step(self) -> tuple:
        
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
