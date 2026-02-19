from django import template
from django.urls import reverse
from django.templatetags.static import static


register = template.Library()

@register.simple_tag(takes_context=True)
def get_sidebar(context):
    request = context.get('request')
    if not request:
        return []

    user = request.user
    url_name = request.resolver_match.url_name if request.resolver_match else None
    
    if user: # Тут повинна бути перевірка користувача (учень, ментор, батько, курс учня)
        # Тестово відображено список пунктів батьків
        # Замість "#" повинні бути назви посилання в "active", та reverse("назва") в "link"
        return [
            {"title": "Дашборд", "active": url_name == "#", "link": "#", "img": static(f'img/sideBar/icons/dashboard.svg')},
            {"title": "Мої Групи", "active": url_name == "#", "link": "#", "img": static(f'img/sideBar/icons/folder.svg')},
            {"title": "Мої Студенти", "active": url_name == "#", "link": "#", "img": static(f'img/sideBar/icons/students.svg')},
            {"title": "Розклад", "active": url_name == "#", "link": "#", "img": static(f'img/sideBar/icons/calendar.svg')},
            {"title": "Рахунки", "active": url_name == "#", "link": "#", "img": static(f'img/sideBar/icons/wallet.svg')}
        ]

    return []