import pytest
from pytest_bdd import given, when, then, parsers
import json
import uuid

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

@when(parsers.parse('Присвоить переменной "{var_name}" значение "{value}"'))
def assign_variable(context, var_name, value):
    if value == "${UUID}":
        value = str(uuid.uuid4())
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоено значение {value}")

@when(parsers.parse('установить переменную "{var_name}" значением "{value}"'))
def set_variable_alias(context, var_name, value):
    assign_variable(context, var_name, value)

@when(parsers.parse('Комментарий "{text}"'))
def add_comment(context, text):
    print(f"COMMENT: {text}")

@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}"'))
def send_rest_request(context, method_path, server_name):
    print(f"MOCK: Отправка {method_path} на сервер {server_name}")
    context["response"] = {
        "status_code": 200,
        "body": {"status": "success"}
    }

@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}" с body из файла "{file_path}"'))
def send_rest_request_from_file(context, method_path, server_name, file_path):
    print(f"MOCK: Отправка {method_path} на сервер {server_name} с телом из {file_path}")
    context["response"] = {
        "status_code": 200,
        "body": {"status": "success", "mocked_from": file_path}
    }

@when(parsers.parse('Загрузить TCR файлы'))
def load_tcr_files(context, datatable):
    print(f"MOCK: Загрузка TCR файлов: {datatable}")

@when(parsers.parse('Выполнить запрос в базу "{db_name}":'))
def execute_sql_query(context, db_name, docstring):
    print(f"MOCK: Выполнение запроса в {db_name}: {docstring}")
    context["last_sql_result"] = [{"count(*)": 1}]

@when(parsers.parse('выполнить SQL запрос в базу "{db_name}":'))
def execute_sql(context, db_name, docstring):
    execute_sql_query(context, db_name, docstring)

@when(parsers.parse('Отправить сообщение в кафку "{kafka_name}" в топик "{topic_name}"'))
def send_kafka_message(context, kafka_name, topic_name, docstring):
    print(f"MOCK: Отправка сообщения в Kafka {kafka_name}, топик {topic_name}: {docstring}")

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

@then(parsers.parse('Проверить ответ с кодом {status_code:d} и body из файла "{file_path}"'))
def check_response_from_file(context, status_code, file_path):
    print(f"MOCK: Проверка ответа {status_code} с телом из {file_path}")
    assert context["response"].get("status_code") == status_code

@then(parsers.parse('Проверить ответ с кодом {status_code:d} и body'))
def check_response_body_json(context, status_code, docstring):
    print(f"MOCK: Проверка ответа {status_code} и JSON body: {docstring}")
    assert context["response"].get("status_code") == status_code

@then(parsers.parse('Проверить результат запроса из базы "{db_name}"'))
def check_sql_result_direct(context, db_name, datatable):
    print(f"MOCK: Проверка результата SQL в {db_name}: {datatable}")
    assert True

@then(parsers.parse('сохранить значение поля "{field}" в переменную "{var_name}"'))
def save_variable(context, field, var_name):
    value = context["response"].get("body", {}).get(field)
    context["variables"][var_name] = value
    print(f"MOCK: Значение {value} из поля {field} сохранено в переменную {var_name}")

@then(parsers.parse('Проверить результат запроса из базы "{db_name}" в течение {timeout:d} секунд'))
def check_sql_result_with_timeout(context, db_name, timeout, datatable):
    print(f"MOCK: Проверка результата SQL в {db_name} (таймаут {timeout}с): {datatable}")
    assert True

@then(parsers.parse('результат запроса в базу "{db_name}" содержит данные в течение {timeout:d} секунд'))
def check_sql_result_contains(context, db_name, timeout, datatable):
    check_sql_result_with_timeout(context, db_name, timeout, datatable)

@then(parsers.parse('Выполнить python код'))
def execute_python_code(context, docstring):
    print(f"MOCK: Выполнение Python кода:\n{docstring}")
    # В моке просто логируем, выполнение реального кода может быть небезопасно или требовать сложной настройки контекста
    pass
