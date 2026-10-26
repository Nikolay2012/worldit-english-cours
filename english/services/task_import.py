import csv
import io

from django.core.files.uploadedfile import UploadedFile

from WorldIT import settings
from english.models.english_task import EnglishTask
from english.services.exceptions import NotFoundError, ConflictError, ValidationError


class TaskImportServices:
    def __init__(self):
        
        # Указываем свои "местные" названия столбцов
        # Таким образом заменяем стандартные столбцы из самого csv файла в которых, 
        # например может быть BOM-метка, которая приведет к поднятию лишних исключений при парсинге
        self.COLUMNS = ["word", "translation", "category", "image_1", "image_2"]
        
        # Обязательные столбцы, без которых создание шагов и вопросов невозможно в принципе
        self.REQUIRED_COLUMNS = ["word", "translation", "category"]
        
        # Макс. поддерживаемый размер csv - мегабайт
        # во избежание загрузки больших файлов, которые, очевидно, 
        # таблицами для курса английского являтся не будут
        self.MAX_CSV_SIZE = 1 * 1024 * 1024
        
        # Количество вариантов ответа в задании типа "Слова"
        # Взято из дизайн-проекта
        self.ANSWER_OPTIONS_COUNT = 6
    
    def import_file(
            self, 
            task_id: int, 
            file: UploadedFile
        ) -> list[dict[str, str]]:
        
        task = self._get_empty_task(task_id=task_id)
        
        self._parse_csv(file=file)
        
    
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
    
    def _parse_csv(self, file: UploadedFile):
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
        
        print(rows)
        
        # return rows
    
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
    
    def _parse_row(
            self, 
            row: list[str], 
            line_num: int
        ) -> dict[str, str]:
        """
        Парс конкретного ряда вынесен в отдельный метод,
        по причине нахождения здесь свойственных только рядок проверок
        
        line_num передан для удобного вывода ряда, 
        на котором csv.reader находится при выводе ошибки
        
        Из ошибок, может подниматься ValidationError
        """
        
        # Пустой ли ряд
        if not any(cell.strip() for cell in row):
            raise ValidationError(f"Рядок {line_num}: порожній рядок")
        
        # Ряды должны быть одной длины
        # В противном случае zip() не запишет часть информации
        # Это приведет к поднятию лишних исключений уже при работе заданий
        if len(row) != len(self.COLUMNS):
            raise ValidationError(f"Рядок {line_num}: рядок має бути довжини {len(self.COLUMNS)}")
        
        data = {}
        
        for column, cell in zip(self.COLUMNS, row):
            data[column] = cell.strip()
        
        for column in self.REQUIRED_COLUMNS:
            # Проверяем, заполнена ли клетка в ряду
            # Если даже одна клетка не заполнена - весь csv не принимается
            if not data[column]:
                raise ValidationError(f"Рядок {line_num}: не заповнене поле «{column}»")
        
        data["category"] = data["category"].lower()
        
        return data
