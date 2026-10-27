"""
Базовый импортёр заданий курса английского из csv файла

Здесь находится общая часть импорта, одинаковая для всех типов заданий:
-Получение задания и проверка, что оно существует и ещё пустое - метод ._get_empty_task()
-Чтение файла и проверка его формата, размера и кодировки - метод ._read_text()
-Парсинг csv по рядкам - метод ._parse_csv()

Конкретный импортёр (например, для задания типа "Слова") наследует этот класс
и сам указывает свои столбцы (COLUMNS, REQUIRED_COLUMNS),
проверку одного ряда (._parse_row())
и запись шагов задания в БД

Метод .import_file() возвращает задание и список рядков,
дальше с ними работает конкретный импортёр

Из ошибок, могут подниматься NotFoundError, ConflictError и ValidationError
"""

import csv
import io

from django.core.files.uploadedfile import UploadedFile

from WorldIT import settings
from english.models.english_task import EnglishTask
from english.services.exceptions import NotFoundError, ConflictError, ValidationError

class BaseEnglishTaskImporter:
    # Макс. поддерживаемый размер csv - мегабайт
    # во избежание загрузки больших файлов, которые, очевидно, 
    # таблицами для курса английского являтся не будут
    MAX_CSV_SIZE = 1 * 1024 * 1024
    
    def import_file(
            self, 
            task_id: int, 
            file: UploadedFile
        ) -> list[dict[str, str]]:
        
        task = self._get_empty_task(task_id=task_id)
        rows = self._parse_csv(file=file)
        
        return (task, rows)
    
    # Получение задания, 
    # в том числе проверка на то, существует ли оно
    def _get_empty_task(self, task_id: int) -> EnglishTask:
        
        # Задание
        task: EnglishTask = EnglishTask.objects.filter(
            pk=task_id,
            lesson__module__course_id=settings.ENGLISH_COURSE_ID
        ).first()
        
        if task is None:
            raise NotFoundError("Завдання не вказане в жодному уроці")
        
        if task.steps.exists():
            raise ConflictError("Завдання вже має завантажені кроки")
        
        return task
    
    def _parse_csv(self, file: UploadedFile) -> list[dict[str, str]]:
        """
        Ключевой метод, выполняющий парсинг csv со словами
        
        Может поднимать (raise) ValidationError (импортированный из english/services/exceptions.py),
        при возникновении ошибок с чтением файла или при невалидном контенте файла
        """
        
        text = self._read_text(file=file)
        
        reader = csv.reader(text)
        
        try:
            # Пропускает заголовки
            # Будут указаны собственные на основе self.COLUMNS
            next(reader)
        except StopIteration:
            raise ValidationError("Файл порожній")
        
        # Отбираем и парсим все рядки csv, 
        # в соответствии с дальнейшим форматом записи в БД
        rows = []
        
        try:
            for row in reader:
                # по причине передачи reader.line_num, указал в самом методе - .parse_row()
                rows.append(
                    self._parse_row(row, reader.line_num)
                )
        except csv.Error as error:
            raise ValidationError(f"Рядок {reader.line_num}: пошкоджений CSV") from error
        
        if not rows:
            raise ValidationError("У файлі немає жодного слова")
        
        return rows
    
    
    def _read_text(self, file: UploadedFile) -> io.StringIO:
        """
        Метод, возвращающий строку для работы csv.reader
        csv.reader не в состоянии работать с байтами, 
        потому необходимо давать ему на входе рядок
        """
        
        if not file.name.lower().endswith(".csv"):
            raise ValidationError("Очікується файл формату .csv")
        
        if file.size == 0 or file.size > self.MAX_CSV_SIZE:
            raise ValidationError("Некоректний розмір файлу")
        
        try:
            # В кодировке добавляем «-sig», для удаления BOM-метки
            # Да бы после парсинга,
            # метка не представляла угрозы для валидности полученных данных
            # Стоить отметить, что в обычном UTF-8 метка BOM не встречается. 
            # Ведь она свойственна для других кодировок, например - UTF-16
            # Но Excel, при импорте, она указывается даже в UTF-8
            return io.StringIO(file.read().decode("utf-8-sig"))
        except UnicodeDecodeError as error:
            raise ValidationError("Файл має бути у кодуванні UTF-8") from error
