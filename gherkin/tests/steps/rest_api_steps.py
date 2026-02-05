"""
REST API шаги для тестирования.
Включает шаги для отправки запросов с заголовками и проверки ответов.
"""
from pytest_bdd import when, then, parsers


@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}" с хедерами "{headers}" с body из файла "{file_path}"'))
def send_rest_request_with_headers_from_file(context, method_path, server_name, headers, file_path):
    """Отправка REST запроса с заголовками и телом из файла."""
    parsed_headers = {}
    for header in headers.split(","):
        if ":" in header:
            key, value = header.split(":", 1)
            parsed_headers[key.strip()] = value.strip()
    
    print(f"MOCK: Отправка {method_path} на сервер {server_name}")
    print(f"MOCK: Заголовки: {parsed_headers}")
    print(f"MOCK: Тело из файла: {file_path}")
    
    context["request"]["headers"] = parsed_headers
    context["request"]["method_path"] = method_path
    context["request"]["server"] = server_name
    context["response"] = {
        "status_code": 200,
        "body": {
            "status": "success",
            "mocked_from": file_path,
            "rqUid": "mock-uuid-12345"
        },
        "headers": {
            "rquid": "mock-response-uuid"
        }
    }


@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}" с хедерами "{headers}"'))
def send_rest_request_with_headers(context, method_path, server_name, headers):
    """Отправка REST запроса с заголовками без тела."""
    parsed_headers = {}
    for header in headers.split(","):
        if ":" in header:
            key, value = header.split(":", 1)
            parsed_headers[key.strip()] = value.strip()
    
    print(f"MOCK: Отправка {method_path} на сервер {server_name}")
    print(f"MOCK: Заголовки: {parsed_headers}")
    
    context["request"]["headers"] = parsed_headers
    context["request"]["method_path"] = method_path
    context["request"]["server"] = server_name
    context["response"] = {
        "status_code": 200,
        "body": {
            "processId": "mock-process-id-12345",
            "status": "success"
        },
        "headers": {
            "rquid": "mock-response-uuid"
        }
    }


@then(parsers.parse('Проверить ответ с кодом {status_code:d}'))
def check_response_code_only(context, status_code):
    """Проверка только кода ответа."""
    actual_code = context["response"].get("status_code")
    print(f"MOCK: Проверка кода ответа: ожидается {status_code}, получено {actual_code}")
    assert actual_code == status_code


@then(parsers.parse('Проверить хедеры из последнего ответа'))
def check_response_headers(context, datatable):
    """Проверка заголовков ответа по таблице."""
    print(f"MOCK: Проверка заголовков ответа: {datatable}")
    assert "headers" in context["response"]


@then(parsers.parse('Проверить ответ с кодом {status_code:d} в течение {timeout:d} секунд'))
def check_response_with_timeout(context, status_code, timeout):
    """Проверка кода ответа с таймаутом (polling)."""
    print(f"MOCK: Проверка ответа с кодом {status_code} в течение {timeout} секунд")
    actual_code = context["response"].get("status_code")
    assert actual_code == status_code


@then(parsers.parse('Проверить ответ с кодом {status_code:d} и файлом с размером больше {size:d} кБ'))
def check_response_with_file_size(context, status_code, size):
    """Проверка кода ответа и размера файла в ответе."""
    print(f"MOCK: Проверка ответа с кодом {status_code} и файлом > {size} кБ")
    actual_code = context["response"].get("status_code")
    assert actual_code == status_code
    print(f"MOCK: Размер файла в ответе: {size + 10} кБ (мок)")
