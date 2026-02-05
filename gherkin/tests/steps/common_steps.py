import pytest
from pytest_bdd import given, when, then, parsers
import json

@pytest.fixture
def context():
    return {
        "request": {},
        "response": {},
        "variables": {}
    }

# --- Given steps ---

@given(parsers.parse('установлен базовый URL "{url}"'))
def set_base_url(context, url):
    context["base_url"] = url
    print(f"MOCK: Базовый URL установлен на {url}")

@given(parsers.parse('заголовок "{name}" имеет значение "{value}"'))
def set_header(context, name, value):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"][name] = value
    print(f"MOCK: Установлен заголовок {name}: {value}")

# --- When steps ---

@when(parsers.parse('отправить POST запрос на "{endpoint}" с телом:'))
def send_post_request_with_body(context, endpoint, docstring):
    body = docstring
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["body"] = json.loads(body)
    
    # Mocking the response
    context["response"] = {
        "status_code": 201,
        "body": {"status": "success", "id": 123, "data": context["request"]["body"]}
    }
    print(f"MOCK: Отправлен POST запрос на {full_url}")

@when(parsers.parse('отправить GET запрос на "{endpoint}"'))
def send_get_request(context, endpoint):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "GET"
    
    # Mocking the response
    context["response"] = {
        "status_code": 200,
        "body": {"id": 123, "name": "Mock Item", "type": "test"}
    }
    print(f"MOCK: Отправлен GET запрос на {full_url}")

# --- Then steps ---

@then(parsers.parse('код ответа должен быть {status_code:d}'))
def check_status_code(context, status_code):
    actual_code = context["response"].get("status_code")
    print(f"MOCK: Проверка кода ответа: ожидается {status_code}, получено {actual_code}")
    assert actual_code == status_code

@then(parsers.parse('тело ответа содержит поле "{field}" со значением "{value}"'))
def check_response_field(context, field, value):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: ожидается {value}, получено {actual_value}")
    assert str(actual_value) == str(value)

@then(parsers.parse('сохранить значение поля "{field}" в переменную "{var_name}"'))
def save_variable(context, field, var_name):
    value = context["response"].get("body", {}).get(field)
    context["variables"][var_name] = value
    print(f"MOCK: Значение {value} из поля {field} сохранено в переменную {var_name}")
