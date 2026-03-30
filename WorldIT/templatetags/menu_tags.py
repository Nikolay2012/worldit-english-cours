from django import template
from django.urls import reverse
from django.templatetags.static import static


register = template.Library()

def create_item(url_name: str, title: str, link: str, img_name: str, sub_items: list[dict] = None) -> dict:
    active = url_name == link
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
    

    if user: 
        list_sub_groups = [{"title": "Мої групи", "link": "my_groups"}]
        if not set(user.account_types).isdisjoint(["mentor", "manager", "admin"]):
            list_sub_groups.append({"title": "Архів груп", "link": "archive_groups"})
        if "admin" in user.account_types:
            list_sub_groups.insert(0, {"title": "Всі групи", "link": "all_groups"})

        list_sub_courses = [{"title": "Всі курси", "link": "all_courses"}, {"title": "Мої курси", "link": "my_courses"}]
        if "student" in user.account_types:
            list_sub_courses.append({"title": "Завершені курси", "link": "completed_courses"})

        list_menu = [ 
            create_item(url_name, "Дашборд", "dashboard", "dashboard"),
            create_item(url_name, "Курси", "my_courses", "rocket", list_sub_courses),
            create_item(url_name, "Групи", "my_groups", "folder", list_sub_groups),
            create_item(url_name, "Розклад", "schedule", "calendar")
        ]
        if "parent" in user.account_types:
            if len(user.account_types) == 1:
                del list_menu[1]
                del list_menu[1]
            list_menu.insert(-1, create_item(url_name, "Мої Студенти", "my_students", "students"))
            list_menu.append(create_item(url_name, "Рахунки", "payment", "wallet"))
        
        if "admin" in user.account_types:
            list_menu.append(create_item(url_name, "Ментори", "mentors", "mentors"))
            list_menu.append(create_item(url_name, "Студенти", "students", "students"))

        return list_menu

    return []

@register.simple_tag(takes_context=True)
def get_header_links(context):
    request = context.get('request')
    if request:
        url_name = request.resolver_match.url_name if request.resolver_match else None
        if url_name == "dashboard":
            return ["Дашборд"]
    return []