
class ValidationError(Exception):
    """
        Помилка валідації даних, надісланих клієнтом
    """
    
    def __init__(self, message: str):
        super().__init__(message)
        
        self.message = message

class NotFoundError(Exception):
    """
        Помилка пошуку та отримання даних
    """
    
    def __init__(self, message: str):
        super().__init__(message)
        
        self.message = message
