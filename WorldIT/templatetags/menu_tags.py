from django import template
from django.urls import reverse
from django.templatetags.static import static
from django.conf import settings

register = template.Library()

@register.filter
def first_word(value):
    return value.split()[0]

def create_item(url_name: str, title: str, link: str, img_name: str, sub_items: list[dict] = None, sub_links: list[str] = None) -> dict:
    active = url_name == link
    if sub_links:
        for sub_link in sub_links:
            if url_name == sub_link:
                active = True

    if sub_items: 
        for item in sub_items:
            item['active'] = url_name == item["link"]
            item["link"] = reverse(item["link"])
            if item['active']: 
                active = True
    return {
        "title": title, 
        "active": active, 
        "link": reverse(link), 
        "img": static(f'img/sideBar/icons/{img_name}.svg'),
        "sub_items": sub_items
    }

@register.simple_tag(takes_context=True)
def get_sidebar(context):
    request = context.get('request')
    if not request:
        return []

    user = request.user
    url_name = request.resolver_match.url_name if request.resolver_match else None
    

    if user and user.is_authenticated: 
        list_menu = []
        if settings.DEBUG or  "admin" in user.account_types:
            list_sub_courses = [{"title": "Всі курси", "link": "all_courses"}, {"title": "Мої курси", "link": "my_courses"}]
            if "student" in user.account_types:
                list_sub_courses.append({"title": "Завершені курси", "link": "completed_courses"})
            
            list_menu = [ 
                create_item(url_name, "Головна", "debug_main", "dashboard"),
                create_item(url_name, "Курси", "my_courses", "rocket", list_sub_courses),
            ]

        return list_menu
    elif user and not user.is_authenticated:
        return create_item(url_name, "Увійти", "login", "login"),

    return []

@register.simple_tag(takes_context=True)
def get_header_links(context):
    request = context.get('request')
    if request:
        url_name = request.resolver_match.url_name if request.resolver_match else None
        # Приклад роботи тегу: if url_name == "dashboard": return ["Дашборд"]
    return []