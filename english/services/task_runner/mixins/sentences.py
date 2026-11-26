"""
Миксин TaskRunner с логикой прохождения задания типа "Речення" студентом

Подключается в TaskRunner, вызывается через словарь методов
в TaskRunner._get_student_next_step() по типу задания ("sentences")
Берёт из TaskRunnerBase общие методы ядра: шаги задания, запись прогресса,
правильные ответы по шагам, последний отвеченный шаг и процент прогресса

Работает одинаково для обоих вариантов предложений ("Скласти" и "Доповнити"):
варианты различаются только в обработчике шага (SentenceHandler)

Правила прохождения:
-одно правильно собранное или дополненное предложение - один правильный ответ
-каждое предложение нужно пройти правильно один раз
-задание выполнено, когда правильно пройдены все предложения
-неверный ответ записывается, но не засчитывается,
и предложение возвращается в одном из следующих шагов
-выборок нет, работа идёт со всеми предложениями задания

Выбор следующего шага - метод ._get_student_sentences_next_step():
-Если в StudentProgress.current_step есть показанный, но не отвеченный шаг -
возвращается он же (обновление страницы не меняет предложение)
-Иначе отбираются кандидаты - метод ._get_sentence_candidates():
    -только предложения без правильного ответа
    (ещё не показанные или отвеченные неверно)
    -без последнего отвеченного предложения, если кандидатов больше одного
-Если кандидатов нет - задание пройдено, шаг None
-Из кандидатов выбирается случайный шаг и записывается в current_step

Возвращаемые данные:
-._get_student_sentences_next_step() - (шаг или None, {"percent", "is_completed"})
"""

import random

from english.models.english_task_step import EnglishTaskStep
from english.services.task_runner.mixins.base import TaskRunnerBase


class SentencesTaskRunnerMixin(TaskRunnerBase):
    
    def _get_student_sentences_next_step(self) -> tuple:
        
        steps = list(self._get_steps())
        progress = self._get_progress_record()
        
        if progress.current_step_id is not None:
            for step in steps:
                # Если студент перешел на следующий шаг и покинул страницу
                # Либо просто обновил страницу
                # Отобразим именно тот шаг, на котором он остановился
                # В противном случае студент мог перейти на следующий шаг, 
                # не ответив на текущем
                if step.id == progress.current_step_id:
                    return step, self._get_student_progress(
                        steps_count=len(steps),
                        progress=progress
                    )
        
        candidates = self._get_sentence_candidates(
            steps=steps,
            correct_by_step=self._get_correct_by_step(),
            last_step_id=self._get_last_answered_step_id()
        )
        
        # Если кандидаты отсутствуют, то задание выполнено
        if not candidates:
            return None, self._get_student_progress(
                steps_count=len(steps),
                progress=progress
            )
        
        # Берем случайны следующий шаг из уже собранного набора кандиатов в следующие шаги
        step = random.choice(candidates)
        
        # Уже полученный шаг выставляется на текущий
        # Так это потому, что этот шаг уже будет отображен юзеру
        progress.current_step = step
        progress.save()
        
        return step, self._get_student_progress(
            steps_count=len(steps),
            progress=progress
        )
    
    def _get_sentence_candidates(
        self,
        steps: list[EnglishTaskStep],
        correct_by_step: dict[int, int],
        last_step_id: int | None
    ) -> list[EnglishTaskStep]:
        
        # Отбираем кандидатов, которых в значении 0
        # Запись такая: id шага: колво правильных ответов 
        # (в случае предложений может быть только 1 прав. ответ. 
        # Т. к. у предложений нету повторов по очередям из 6, как это происходит у слов)
        # Таким образом, в кандидаты попадают только те шаги, 
        # на которые не был дан правильный ответ (либо ответа не было в принципе, т. е. предложения которые ещё не были показаны)
        candidates = [
            step for step in steps
            if correct_by_step.get(step.id, 0) == 0
        ]
        
        if len(candidates) > 1:
            # Последний отвеченный шаг не показываем сразу ещё раз,
            # но только если есть другие кандидаты:
            # если он остался единственным непройденным - показываем его снова
            candidates = [
                step for step in candidates
                if step.id != last_step_id
            ]
        
        return candidates
