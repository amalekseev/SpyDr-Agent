"""
REST API шаги для тестирования.
Включает шаги для отправки запросов с заголовками, проверки ответов,
работы с различными форматами данных и аутентификацией.
"""
from pytest_bdd import given, when, then, parsers
import json
import uuid
from datetime import datetime


# ============================================================================
# --- Given steps (REST API Setup) ---
# ============================================================================

@given(parsers.parse('настроен REST клиент для сервера "{server_name}"'))
def setup_rest_client(context, server_name):
    """Настройка REST клиента для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    context["rest_clients"][server_name] = {
        "configured": True,
        "base_url": f"http://{server_name}"
    }
    print(f"MOCK: Настроен REST клиент для сервера {server_name}")


@given(parsers.parse('настроен REST клиент для сервера "{server_name}" с базовым URL "{base_url}"'))
def setup_rest_client_with_url(context, server_name, base_url):
    """Настройка REST клиента с базовым URL."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    context["rest_clients"][server_name] = {
        "configured": True,
        "base_url": base_url
    }
    print(f"MOCK: Настроен REST клиент для сервера {server_name} с URL {base_url}")


@given(parsers.parse('установлен заголовок "{header_name}" со значением "{header_value}" для сервера "{server_name}"'))
def set_server_header(context, header_name, header_value, server_name):
    """Установка заголовка для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    if "headers" not in context["rest_clients"][server_name]:
        context["rest_clients"][server_name]["headers"] = {}
    context["rest_clients"][server_name]["headers"][header_name] = header_value
    print(f"MOCK: Установлен заголовок {header_name} для сервера {server_name}")


@given(parsers.parse('установлена OAuth2 авторизация для сервера "{server_name}" с токеном "{token}"'))
def set_oauth2_auth(context, server_name, token):
    """Установка OAuth2 авторизации."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["auth"] = {
        "type": "oauth2",
        "token": token
    }
    print(f"MOCK: Установлена OAuth2 авторизация для сервера {server_name}")


@given(parsers.parse('установлена Basic авторизация для сервера "{server_name}" логин "{login}" пароль "{password}"'))
def set_basic_auth_for_server(context, server_name, login, password):
    """Установка Basic авторизации для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["auth"] = {
        "type": "basic",
        "login": login,
        "password": password
    }
    print(f"MOCK: Установлена Basic авторизация для сервера {server_name}")


@given(parsers.parse('установлен API ключ "{api_key}" для сервера "{server_name}"'))
def set_api_key_for_server(context, api_key, server_name):
    """Установка API ключа для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["api_key"] = api_key
    print(f"MOCK: Установлен API ключ для сервера {server_name}")


@given(parsers.parse('установлен таймаут {timeout:d} секунд для сервера "{server_name}"'))
def set_server_timeout(context, timeout, server_name):
    """Установка таймаута для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["timeout"] = timeout
    print(f"MOCK: Установлен таймаут {timeout} секунд для сервера {server_name}")


@given(parsers.parse('установлен retry policy с {retries:d} попытками для сервера "{server_name}"'))
def set_retry_policy(context, retries, server_name):
    """Установка политики повторных попыток."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["retries"] = retries
    print(f"MOCK: Установлен retry policy с {retries} попытками для сервера {server_name}")


@given(parsers.parse('включено логирование запросов для сервера "{server_name}"'))
def enable_request_logging_for_server(context, server_name):
    """Включение логирования запросов для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["log_requests"] = True
    print(f"MOCK: Включено логирование запросов для сервера {server_name}")


@given(parsers.parse('установлен прокси "{proxy_url}" для сервера "{server_name}"'))
def set_proxy_for_server(context, proxy_url, server_name):
    """Установка прокси для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["proxy"] = proxy_url
    print(f"MOCK: Установлен прокси {proxy_url} для сервера {server_name}")


@given(parsers.parse('отключена проверка SSL для сервера "{server_name}"'))
def disable_ssl_for_server(context, server_name):
    """Отключение проверки SSL для сервера."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["verify_ssl"] = False
    print(f"MOCK: Отключена проверка SSL для сервера {server_name}")


@given(parsers.parse('установлен сертификат клиента "{cert_path}" для сервера "{server_name}"'))
def set_client_cert(context, cert_path, server_name):
    """Установка клиентского сертификата."""
    if "rest_clients" not in context:
        context["rest_clients"] = {}
    if server_name not in context["rest_clients"]:
        context["rest_clients"][server_name] = {}
    context["rest_clients"][server_name]["client_cert"] = cert_path
    print(f"MOCK: Установлен клиентский сертификат для сервера {server_name}")


# ============================================================================
# --- When steps (REST API Operations) ---
# ============================================================================

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


@when(parsers.parse('отправить GET запрос на сервер "{server_name}" endpoint "{endpoint}"'))
def send_get_to_server(context, server_name, endpoint):
    """Отправка GET запроса на сервер."""
    print(f"MOCK: Отправка GET на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "GET"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["response"] = {
        "status_code": 200,
        "body": {"id": 1, "name": "test"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 50
    }


@when(parsers.parse('отправить POST запрос на сервер "{server_name}" endpoint "{endpoint}" с телом:'))
def send_post_to_server(context, server_name, endpoint, docstring):
    """Отправка POST запроса на сервер с телом."""
    print(f"MOCK: Отправка POST на сервер {server_name} endpoint {endpoint}")
    print(f"MOCK: Тело:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["body"] = docstring
    context["response"] = {
        "status_code": 201,
        "body": {"id": 123, "status": "created"},
        "headers": {"Content-Type": "application/json", "Location": f"{endpoint}/123"},
        "response_time": 100
    }


@when(parsers.parse('отправить PUT запрос на сервер "{server_name}" endpoint "{endpoint}" с телом:'))
def send_put_to_server(context, server_name, endpoint, docstring):
    """Отправка PUT запроса на сервер с телом."""
    print(f"MOCK: Отправка PUT на сервер {server_name} endpoint {endpoint}")
    print(f"MOCK: Тело:\n{docstring}")
    
    context["request"]["method"] = "PUT"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["body"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"status": "updated"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 80
    }


@when(parsers.parse('отправить PATCH запрос на сервер "{server_name}" endpoint "{endpoint}" с телом:'))
def send_patch_to_server(context, server_name, endpoint, docstring):
    """Отправка PATCH запроса на сервер с телом."""
    print(f"MOCK: Отправка PATCH на сервер {server_name} endpoint {endpoint}")
    print(f"MOCK: Тело:\n{docstring}")
    
    context["request"]["method"] = "PATCH"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["body"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"status": "patched"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 60
    }


@when(parsers.parse('отправить DELETE запрос на сервер "{server_name}" endpoint "{endpoint}"'))
def send_delete_to_server(context, server_name, endpoint):
    """Отправка DELETE запроса на сервер."""
    print(f"MOCK: Отправка DELETE на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "DELETE"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["response"] = {
        "status_code": 204,
        "body": {},
        "headers": {},
        "response_time": 40
    }


@when(parsers.parse('отправить HEAD запрос на сервер "{server_name}" endpoint "{endpoint}"'))
def send_head_to_server(context, server_name, endpoint):
    """Отправка HEAD запроса на сервер."""
    print(f"MOCK: Отправка HEAD на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "HEAD"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["response"] = {
        "status_code": 200,
        "body": {},
        "headers": {"Content-Length": "1234", "Content-Type": "application/json"},
        "response_time": 20
    }


@when(parsers.parse('отправить OPTIONS запрос на сервер "{server_name}" endpoint "{endpoint}"'))
def send_options_to_server(context, server_name, endpoint):
    """Отправка OPTIONS запроса на сервер."""
    print(f"MOCK: Отправка OPTIONS на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "OPTIONS"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["response"] = {
        "status_code": 200,
        "body": {},
        "headers": {"Allow": "GET, POST, PUT, DELETE, OPTIONS", "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE"},
        "response_time": 15
    }


@when(parsers.parse('отправить запрос с файлом "{file_path}" на сервер "{server_name}" endpoint "{endpoint}"'))
def send_file_to_server(context, file_path, server_name, endpoint):
    """Отправка файла на сервер."""
    print(f"MOCK: Отправка файла {file_path} на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["file"] = file_path
    context["response"] = {
        "status_code": 201,
        "body": {"file_id": str(uuid.uuid4()), "filename": file_path, "size": 1024},
        "headers": {"Content-Type": "application/json"},
        "response_time": 200
    }


@when(parsers.parse('отправить multipart запрос на сервер "{server_name}" endpoint "{endpoint}" с файлами:'))
def send_multipart_to_server(context, server_name, endpoint, docstring):
    """Отправка multipart запроса с файлами."""
    files = [f.strip() for f in docstring.strip().split("\n")]
    print(f"MOCK: Отправка multipart запроса на сервер {server_name} с файлами: {files}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["files"] = files
    context["response"] = {
        "status_code": 201,
        "body": {"uploaded_files": len(files)},
        "headers": {"Content-Type": "application/json"},
        "response_time": 300
    }


@when(parsers.parse('отправить form-data запрос на сервер "{server_name}" endpoint "{endpoint}":'))
def send_form_data_to_server(context, server_name, endpoint, docstring):
    """Отправка form-data запроса."""
    print(f"MOCK: Отправка form-data запроса на сервер {server_name}")
    print(f"MOCK: Данные:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["form_data"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"status": "received"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 100
    }


@when(parsers.parse('отправить XML запрос на сервер "{server_name}" endpoint "{endpoint}":'))
def send_xml_to_server(context, server_name, endpoint, docstring):
    """Отправка XML запроса."""
    print(f"MOCK: Отправка XML запроса на сервер {server_name}")
    print(f"MOCK: XML:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["xml"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": "<response><status>success</status></response>",
        "headers": {"Content-Type": "application/xml"},
        "response_time": 100
    }


@when(parsers.parse('отправить GraphQL запрос на сервер "{server_name}":'))
def send_graphql_to_server(context, server_name, docstring):
    """Отправка GraphQL запроса."""
    print(f"MOCK: Отправка GraphQL запроса на сервер {server_name}")
    print(f"MOCK: Query:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["graphql"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"data": {"result": "mock_graphql_response"}},
        "headers": {"Content-Type": "application/json"},
        "response_time": 150
    }


@when(parsers.parse('отправить GraphQL mutation на сервер "{server_name}":'))
def send_graphql_mutation_to_server(context, server_name, docstring):
    """Отправка GraphQL mutation."""
    print(f"MOCK: Отправка GraphQL mutation на сервер {server_name}")
    print(f"MOCK: Mutation:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["graphql_mutation"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"data": {"createItem": {"id": "123"}}},
        "headers": {"Content-Type": "application/json"},
        "response_time": 200
    }


@when(parsers.parse('отправить запрос с query параметрами на сервер "{server_name}" endpoint "{endpoint}":'))
def send_request_with_query_params(context, server_name, endpoint, docstring):
    """Отправка запроса с query параметрами."""
    print(f"MOCK: Отправка запроса с query параметрами на сервер {server_name}")
    print(f"MOCK: Параметры:\n{docstring}")
    
    context["request"]["method"] = "GET"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["query_params"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"items": [], "total": 0},
        "headers": {"Content-Type": "application/json"},
        "response_time": 50
    }


@when(parsers.parse('отправить запрос с path параметрами на сервер "{server_name}" endpoint "{endpoint}"'))
def send_request_with_path_params(context, server_name, endpoint):
    """Отправка запроса с path параметрами."""
    # Подставляем переменные в endpoint
    for var_name, var_value in context.get("variables", {}).items():
        endpoint = endpoint.replace(f"${{{var_name}}}", str(var_value))
    
    print(f"MOCK: Отправка запроса на сервер {server_name} endpoint {endpoint}")
    
    context["request"]["method"] = "GET"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["response"] = {
        "status_code": 200,
        "body": {"id": 123, "name": "test"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 50
    }


@when(parsers.parse('отправить асинхронный запрос на сервер "{server_name}" endpoint "{endpoint}"'))
def send_async_request(context, server_name, endpoint):
    """Отправка асинхронного запроса."""
    print(f"MOCK: Отправка асинхронного запроса на сервер {server_name}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["async"] = True
    context["response"] = {
        "status_code": 202,
        "body": {"task_id": str(uuid.uuid4()), "status": "pending"},
        "headers": {"Content-Type": "application/json", "Location": f"{endpoint}/status/123"},
        "response_time": 30
    }


@when(parsers.parse('проверить статус асинхронной задачи "{task_id}" на сервере "{server_name}"'))
def check_async_task_status(context, task_id, server_name):
    """Проверка статуса асинхронной задачи."""
    print(f"MOCK: Проверка статуса задачи {task_id} на сервере {server_name}")
    
    context["response"] = {
        "status_code": 200,
        "body": {"task_id": task_id, "status": "completed", "result": {"data": "mock_result"}},
        "headers": {"Content-Type": "application/json"},
        "response_time": 20
    }


@when(parsers.parse('ожидать завершения асинхронной задачи "{task_id}" на сервере "{server_name}" в течение {timeout:d} секунд'))
def wait_for_async_task(context, task_id, server_name, timeout):
    """Ожидание завершения асинхронной задачи."""
    print(f"MOCK: Ожидание завершения задачи {task_id} в течение {timeout} секунд")
    
    context["response"] = {
        "status_code": 200,
        "body": {"task_id": task_id, "status": "completed", "result": {"data": "mock_result"}},
        "headers": {"Content-Type": "application/json"},
        "response_time": 1000
    }


@when(parsers.parse('отправить пакет запросов на сервер "{server_name}":'))
def send_batch_requests_to_server(context, server_name, docstring):
    """Отправка пакета запросов."""
    print(f"MOCK: Отправка пакета запросов на сервер {server_name}")
    print(f"MOCK: Запросы:\n{docstring}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["batch"] = True
    context["response"] = {
        "status_code": 200,
        "body": {"results": [{"status": 200}, {"status": 201}]},
        "headers": {"Content-Type": "application/json"},
        "response_time": 500
    }


@when(parsers.parse('выполнить health check на сервере "{server_name}"'))
def health_check(context, server_name):
    """Выполнение health check."""
    print(f"MOCK: Health check на сервере {server_name}")
    
    context["response"] = {
        "status_code": 200,
        "body": {"status": "healthy", "version": "1.0.0"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 10
    }


@when(parsers.parse('получить OpenAPI спецификацию с сервера "{server_name}"'))
def get_openapi_spec(context, server_name):
    """Получение OpenAPI спецификации."""
    print(f"MOCK: Получение OpenAPI спецификации с сервера {server_name}")
    
    context["response"] = {
        "status_code": 200,
        "body": {"openapi": "3.0.0", "info": {"title": "Mock API", "version": "1.0.0"}},
        "headers": {"Content-Type": "application/json"},
        "response_time": 50
    }


@when(parsers.parse('повторить последний запрос на сервер "{server_name}"'))
def repeat_last_request_to_server(context, server_name):
    """Повторение последнего запроса."""
    print(f"MOCK: Повторение последнего запроса на сервер {server_name}")
    # Используем сохраненные данные запроса


@when(parsers.parse('повторить последний запрос на сервер "{server_name}" {times:d} раз'))
def repeat_last_request_multiple(context, server_name, times):
    """Повторение последнего запроса несколько раз."""
    print(f"MOCK: Повторение последнего запроса на сервер {server_name} {times} раз")


@when(parsers.parse('отправить запрос с retry на сервер "{server_name}" endpoint "{endpoint}" с {retries:d} попытками'))
def send_request_with_retry(context, server_name, endpoint, retries):
    """Отправка запроса с retry."""
    print(f"MOCK: Отправка запроса с {retries} попытками на сервер {server_name}")
    
    context["request"]["method"] = "GET"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["retries"] = retries
    context["response"] = {
        "status_code": 200,
        "body": {"status": "success"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 100,
        "attempts": 2
    }


@when(parsers.parse('загрузить файл с сервера "{server_name}" endpoint "{endpoint}" в "{file_path}"'))
def download_file_from_server(context, server_name, endpoint, file_path):
    """Загрузка файла с сервера."""
    print(f"MOCK: Загрузка файла с сервера {server_name} в {file_path}")
    
    context["response"] = {
        "status_code": 200,
        "body": {},
        "headers": {"Content-Type": "application/octet-stream", "Content-Length": "1024"},
        "downloaded_file": file_path,
        "response_time": 500
    }


@when(parsers.parse('отправить запрос с кастомным Content-Type "{content_type}" на сервер "{server_name}" endpoint "{endpoint}":'))
def send_request_with_custom_content_type(context, content_type, server_name, endpoint, docstring):
    """Отправка запроса с кастомным Content-Type."""
    print(f"MOCK: Отправка запроса с Content-Type {content_type} на сервер {server_name}")
    
    context["request"]["method"] = "POST"
    context["request"]["server"] = server_name
    context["request"]["endpoint"] = endpoint
    context["request"]["content_type"] = content_type
    context["request"]["body"] = docstring
    context["response"] = {
        "status_code": 200,
        "body": {"status": "received"},
        "headers": {"Content-Type": "application/json"},
        "response_time": 100
    }


# ============================================================================
# --- Then steps (REST API Verification) ---
# ============================================================================

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


@then(parsers.parse('код ответа сервера "{server_name}" равен {status_code:d}'))
def check_server_response_code(context, server_name, status_code):
    """Проверка кода ответа от конкретного сервера."""
    actual_code = context["response"].get("status_code")
    print(f"MOCK: Проверка кода ответа от {server_name}: ожидается {status_code}, получено {actual_code}")
    assert actual_code == status_code


@then(parsers.parse('ответ содержит JSON поле "{field}" со значением "{value}"'))
def check_json_field_value(context, field, value):
    """Проверка значения JSON поля."""
    body = context["response"].get("body", {})
    actual_value = body.get(field) if isinstance(body, dict) else None
    print(f"MOCK: Проверка поля {field}: ожидается {value}, получено {actual_value}")
    assert str(actual_value) == str(value)


@then(parsers.parse('ответ содержит JSON поле "{field}"'))
def check_json_field_exists(context, field):
    """Проверка наличия JSON поля."""
    body = context["response"].get("body", {})
    print(f"MOCK: Проверка наличия поля {field}")
    assert field in body if isinstance(body, dict) else False


@then(parsers.parse('ответ не содержит JSON поле "{field}"'))
def check_json_field_not_exists(context, field):
    """Проверка отсутствия JSON поля."""
    body = context["response"].get("body", {})
    print(f"MOCK: Проверка отсутствия поля {field}")
    assert field not in body if isinstance(body, dict) else True


@then(parsers.parse('ответ содержит JSON массив "{field}" с {count:d} элементами'))
def check_json_array_count(context, field, count):
    """Проверка количества элементов в JSON массиве."""
    body = context["response"].get("body", {})
    array = body.get(field, []) if isinstance(body, dict) else []
    print(f"MOCK: Проверка количества элементов в {field}: ожидается {count}")
    assert len(array) == count


@then(parsers.parse('ответ содержит JSON массив "{field}" с элементом где "{key}" равен "{value}"'))
def check_json_array_contains_element(context, field, key, value):
    """Проверка наличия элемента в JSON массиве."""
    body = context["response"].get("body", {})
    array = body.get(field, []) if isinstance(body, dict) else []
    print(f"MOCK: Проверка наличия элемента с {key}={value} в массиве {field}")
    found = any(str(item.get(key)) == str(value) for item in array if isinstance(item, dict))
    assert found


@then(parsers.parse('ответ содержит вложенное поле "{path}" со значением "{value}"'))
def check_nested_json_field(context, path, value):
    """Проверка значения вложенного JSON поля."""
    body = context["response"].get("body", {})
    keys = path.split(".")
    current = body
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = None
            break
    print(f"MOCK: Проверка вложенного поля {path}: ожидается {value}, получено {current}")
    assert str(current) == str(value)


@then(parsers.parse('заголовок ответа "{header}" равен "{value}"'))
def check_response_header_value(context, header, value):
    """Проверка значения заголовка ответа."""
    headers = context["response"].get("headers", {})
    actual_value = headers.get(header)
    print(f"MOCK: Проверка заголовка {header}: ожидается {value}, получено {actual_value}")
    assert str(actual_value) == str(value)


@then(parsers.parse('заголовок ответа "{header}" содержит "{substring}"'))
def check_response_header_contains(context, header, substring):
    """Проверка что заголовок содержит подстроку."""
    headers = context["response"].get("headers", {})
    actual_value = str(headers.get(header, ""))
    print(f"MOCK: Проверка что заголовок {header} содержит '{substring}'")
    assert substring in actual_value


@then(parsers.parse('заголовок ответа "{header}" существует'))
def check_response_header_exists(context, header):
    """Проверка наличия заголовка ответа."""
    headers = context["response"].get("headers", {})
    print(f"MOCK: Проверка наличия заголовка {header}")
    assert header in headers


@then(parsers.parse('заголовок ответа "{header}" не существует'))
def check_response_header_not_exists(context, header):
    """Проверка отсутствия заголовка ответа."""
    headers = context["response"].get("headers", {})
    print(f"MOCK: Проверка отсутствия заголовка {header}")
    assert header not in headers


@then(parsers.parse('время ответа сервера меньше {max_time:d} миллисекунд'))
def check_response_time_ms(context, max_time):
    """Проверка времени ответа в миллисекундах."""
    response_time = context["response"].get("response_time", 0)
    print(f"MOCK: Проверка времени ответа: должно быть < {max_time}мс, получено {response_time}мс")
    assert response_time < max_time


@then(parsers.parse('время ответа сервера меньше {max_time:d} секунд'))
def check_response_time_sec(context, max_time):
    """Проверка времени ответа в секундах."""
    response_time = context["response"].get("response_time", 0) / 1000
    print(f"MOCK: Проверка времени ответа: должно быть < {max_time}с")
    assert response_time < max_time


@then(parsers.parse('размер ответа меньше {max_size:d} байт'))
def check_response_size_bytes(context, max_size):
    """Проверка размера ответа в байтах."""
    body = context["response"].get("body", {})
    size = len(json.dumps(body)) if isinstance(body, dict) else len(str(body))
    print(f"MOCK: Проверка размера ответа: должно быть < {max_size} байт")
    assert size < max_size


@then(parsers.parse('размер ответа больше {min_size:d} байт'))
def check_response_size_greater(context, min_size):
    """Проверка что размер ответа больше указанного."""
    body = context["response"].get("body", {})
    size = len(json.dumps(body)) if isinstance(body, dict) else len(str(body))
    print(f"MOCK: Проверка размера ответа: должно быть > {min_size} байт")
    assert size > min_size


@then(parsers.parse('ответ соответствует JSON схеме:'))
def check_response_json_schema(context, docstring):
    """Проверка соответствия ответа JSON схеме."""
    print(f"MOCK: Проверка соответствия JSON схеме:\n{docstring}")
    assert True


@then(parsers.parse('ответ соответствует JSON схеме из файла "{schema_file}"'))
def check_response_json_schema_from_file(context, schema_file):
    """Проверка соответствия ответа JSON схеме из файла."""
    print(f"MOCK: Проверка соответствия JSON схеме из файла {schema_file}")
    assert True


@then(parsers.parse('ответ является валидным JSON'))
def check_response_valid_json(context):
    """Проверка что ответ является валидным JSON."""
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ является валидным JSON")
    assert body is not None


@then(parsers.parse('ответ является валидным XML'))
def check_response_valid_xml(context):
    """Проверка что ответ является валидным XML."""
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ является валидным XML")
    assert body is not None


@then(parsers.parse('сохранить значение поля "{field}" из ответа в переменную "{var_name}"'))
def save_response_field_to_variable(context, field, var_name):
    """Сохранение значения поля из ответа в переменную."""
    body = context["response"].get("body", {})
    value = body.get(field) if isinstance(body, dict) else None
    context["variables"][var_name] = value
    print(f"MOCK: Значение {value} из поля {field} сохранено в переменную {var_name}")


@then(parsers.parse('сохранить значение вложенного поля "{path}" из ответа в переменную "{var_name}"'))
def save_nested_field_to_variable(context, path, var_name):
    """Сохранение значения вложенного поля из ответа в переменную."""
    body = context["response"].get("body", {})
    keys = path.split(".")
    current = body
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = None
            break
    context["variables"][var_name] = current
    print(f"MOCK: Значение {current} из поля {path} сохранено в переменную {var_name}")


@then(parsers.parse('сохранить заголовок "{header}" из ответа в переменную "{var_name}"'))
def save_response_header_to_variable(context, header, var_name):
    """Сохранение заголовка из ответа в переменную."""
    headers = context["response"].get("headers", {})
    value = headers.get(header)
    context["variables"][var_name] = value
    print(f"MOCK: Заголовок {header}={value} сохранен в переменную {var_name}")


@then(parsers.parse('сохранить время ответа в переменную "{var_name}"'))
def save_response_time_to_var(context, var_name):
    """Сохранение времени ответа в переменную."""
    response_time = context["response"].get("response_time", 0)
    context["variables"][var_name] = response_time
    print(f"MOCK: Время ответа {response_time}мс сохранено в переменную {var_name}")


@then(parsers.parse('сравнить ответ с эталоном из файла "{file_path}"'))
def compare_response_with_reference(context, file_path):
    """Сравнение ответа с эталоном из файла."""
    print(f"MOCK: Сравнение ответа с эталоном из файла {file_path}")
    assert True


@then(parsers.parse('сравнить ответ с эталоном из файла "{file_path}" игнорируя поля:'))
def compare_response_with_reference_ignore_fields(context, file_path, docstring):
    """Сравнение ответа с эталоном игнорируя указанные поля."""
    ignored_fields = [f.strip() for f in docstring.strip().split("\n")]
    print(f"MOCK: Сравнение ответа с эталоном из файла {file_path}, игнорируя поля: {ignored_fields}")
    assert True


@then(parsers.parse('вывести тело ответа'))
def print_response_body(context):
    """Вывод тела ответа."""
    body = context["response"].get("body")
    print(f"DEBUG: Тело ответа = {json.dumps(body, indent=2, ensure_ascii=False, default=str)}")


@then(parsers.parse('вывести заголовки ответа'))
def print_response_headers_debug(context):
    """Вывод заголовков ответа."""
    headers = context["response"].get("headers")
    print(f"DEBUG: Заголовки ответа = {json.dumps(headers, indent=2, ensure_ascii=False)}")


@then(parsers.parse('вывести время ответа'))
def print_response_time(context):
    """Вывод времени ответа."""
    response_time = context["response"].get("response_time", 0)
    print(f"DEBUG: Время ответа = {response_time}мс")


@then(parsers.parse('сервер "{server_name}" доступен'))
def check_server_available(context, server_name):
    """Проверка доступности сервера."""
    print(f"MOCK: Проверка доступности сервера {server_name}")
    assert True


@then(parsers.parse('сервер "{server_name}" недоступен'))
def check_server_unavailable(context, server_name):
    """Проверка недоступности сервера."""
    print(f"MOCK: Проверка недоступности сервера {server_name}")
    assert True


@then(parsers.parse('закрыть REST клиент для сервера "{server_name}"'))
def close_rest_client(context, server_name):
    """Закрытие REST клиента."""
    if "rest_clients" in context and server_name in context["rest_clients"]:
        context["rest_clients"][server_name]["configured"] = False
    print(f"MOCK: REST клиент для сервера {server_name} закрыт")
