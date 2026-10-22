from english.models.english_task import EnglishTask
from english.models.open_english_task import OpenEnglishTask
from users.models import Student


class EnglishTaskServices:
    
    @staticmethod
    def can_access_english_task(
            student: Student, 
            task: EnglishTask
        ):
        
        return (
            task.is_available
            # and OpenEnglishTask(...).exists()
        )
