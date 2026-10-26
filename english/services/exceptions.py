"""
Винятки сервісного шару застосунку english.

Сервіси піднімають ці винятки, коли операцію неможливо виконати
з причини, яку можна пояснити користувачу. Ендпоінти перехоплюють їх
і перетворюють на JSON-відповіді з відповідним статусом:

    ValidationError  → 400  некоректні дані від клієнта
    NotFoundError    → 404  об'єкт не знайдено або він не належить вказаному батьківському об'єкту
    ConflictError    → 409  дію неможливо виконати через поточний стан даних

Текст повідомлення (message) показується користувачу,
тому він має бути зрозумілим і без технічних деталей.
"""

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

class ConflictError(Exception):
    """
        Помилка конфлікту
        Може бути використана під час виокремлення конфлікту у запису даних до БД
        Наприклад: при спробі додати кроки для завдання, 
        у випадку, коли вони вже існують - ConflictError
    """
    
    def __init__(self, message: str):
        super().__init__(message)
        
        self.message = message
