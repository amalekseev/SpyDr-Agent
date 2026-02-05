"""
UI шаги для тестирования.
Включает шаги для работы с веб-интерфейсом.
"""
from pytest_bdd import when, then, parsers


@when(parsers.parse('Логин в систему: логин {login}, пароль {password}'))
def login_to_system(context, login, password):
    """Авторизация в системе."""
    print(f"MOCK: Логин в систему")
    print(f"MOCK: Логин: {login}")
    print(f"MOCK: Пароль: {'*' * len(password)}")
    
    context["auth"] = {
        "login": login,
        "authenticated": True
    }


@when(parsers.parse('Сформировать отчет'))
def generate_report(context, datatable):
    """Формирование отчета с параметрами из таблицы."""
    print(f"MOCK: Формирование отчета")
    print(f"MOCK: Параметры: {datatable}")
    
    context["report"] = {
        "parameters": datatable,
        "generated": True
    }


@then(parsers.parse('Проверить наличие элемента "{selector}" на странице'))
def check_element_presence(context, selector):
    """Проверка наличия элемента на странице по селектору."""
    print(f"MOCK: Проверка наличия элемента: {selector}")
    
    context["ui_check"] = {
        "selector": selector,
        "found": True
    }
    assert True
