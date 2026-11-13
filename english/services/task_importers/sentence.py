"""

"""

from django.core.files.uploadedfile import UploadedFile

from english.services.task_importers.base import BaseEnglishTaskImporter


class SentenceImporter(BaseEnglishTaskImporter):
    
    def import_file(
            self, 
            task_id: int,
            file: UploadedFile
        ) -> list[dict[str, str]]:
        
        return {
            "sentences": [
                {
                    "step_id": 1,
                    "answer": "Anna goes to the park every Sunday.",
                    "prompt": "Анна ходить до парку щонеділі.",
                    "template": "",
                },
                {
                    "step_id": 2,
                    "answer": "She likes to walk and listen to music.",
                    "prompt": "Вона любить гуляти та слухати музику.",
                    "template": "",
                },
                {
                    "step_id": 3,
                    "answer": "Sometimes she meets her friends there.",
                    "prompt": "Іноді вона зустрічає там своїх друзів.",
                    "template": "",
                },
                {
                    "step_id": 4,
                    "answer": "She feels happy after spending time outside.",
                    "prompt": "Вона почувається щасливою, провівши час надворі.",
                    "template": "",
                },
                {
                    "step_id": 5,
                    "answer": "They sit on a bench and talk together.",
                    "prompt": "Вони сидять на лавці та розмовляють.",
                    "template": "",
                },
            ],
            "required_correct_answers": 6,
        }
