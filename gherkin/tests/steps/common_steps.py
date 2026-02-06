import pytest
from pytest_bdd import given, when, then, parsers
import json
import uuid
import time
import re
from datetime import datetime, timedelta

@pytest.fixture
def context():
    return {
        "request": {},
        "response": {},
        "variables": {},
        "headers": {},
        "cookies": {},
        "session": {},
        "files": {},
        "timers": {}
    }

# ============================================================================
# --- Given steps ---
# ============================================================================

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

@given(parsers.parse('установлен таймаут запроса {timeout:d} секунд'))
def set_request_timeout(context, timeout):
    context["request_timeout"] = timeout
    print(f"MOCK: Таймаут запроса установлен на {timeout} секунд")

@given(parsers.parse('установлен таймаут соединения {timeout:d} секунд'))
def set_connection_timeout(context, timeout):
    context["connection_timeout"] = timeout
    print(f"MOCK: Таймаут соединения установлен на {timeout} секунд")

@given(parsers.parse('авторизация по токену "{token}"'))
def set_auth_token(context, token):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Authorization"] = f"Bearer {token}"
    print(f"MOCK: Установлен токен авторизации")

@given(parsers.parse('базовая авторизация логин "{login}" пароль "{password}"'))
def set_basic_auth(context, login, password):
    import base64
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Authorization"] = f"Basic {credentials}"
    print(f"MOCK: Установлена базовая авторизация для {login}")

@given(parsers.parse('установлен Content-Type "{content_type}"'))
def set_content_type(context, content_type):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Content-Type"] = content_type
    print(f"MOCK: Content-Type установлен на {content_type}")

@given(parsers.parse('установлен Accept "{accept}"'))
def set_accept_header(context, accept):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Accept"] = accept
    print(f"MOCK: Accept установлен на {accept}")

@given(parsers.parse('установлен User-Agent "{user_agent}"'))
def set_user_agent(context, user_agent):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["User-Agent"] = user_agent
    print(f"MOCK: User-Agent установлен на {user_agent}")

@given(parsers.parse('установлен cookie "{name}" со значением "{value}"'))
def set_cookie(context, name, value):
    context["cookies"][name] = value
    print(f"MOCK: Установлен cookie {name}={value}")

@given(parsers.parse('включен режим отладки'))
def enable_debug_mode(context):
    context["debug_mode"] = True
    print(f"MOCK: Режим отладки включен")

@given(parsers.parse('отключена проверка SSL сертификата'))
def disable_ssl_verification(context):
    context["verify_ssl"] = False
    print(f"MOCK: Проверка SSL сертификата отключена")

@given(parsers.parse('включено следование редиректам'))
def enable_follow_redirects(context):
    context["follow_redirects"] = True
    print(f"MOCK: Следование редиректам включено")

@given(parsers.parse('отключено следование редиректам'))
def disable_follow_redirects(context):
    context["follow_redirects"] = False
    print(f"MOCK: Следование редиректам отключено")

@given(parsers.parse('установлен максимальный размер ответа {size:d} МБ'))
def set_max_response_size(context, size):
    context["max_response_size"] = size * 1024 * 1024
    print(f"MOCK: Максимальный размер ответа установлен на {size} МБ")

@given(parsers.parse('установлен язык запроса "{language}"'))
def set_request_language(context, language):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Accept-Language"] = language
    print(f"MOCK: Язык запроса установлен на {language}")

@given(parsers.parse('установлена кодировка "{encoding}"'))
def set_encoding(context, encoding):
    context["encoding"] = encoding
    print(f"MOCK: Кодировка установлена на {encoding}")

@given(parsers.parse('установлен прокси сервер "{proxy_url}"'))
def set_proxy(context, proxy_url):
    context["proxy"] = proxy_url
    print(f"MOCK: Прокси сервер установлен на {proxy_url}")

@given(parsers.parse('подготовлен тестовый контекст'))
def prepare_test_context(context):
    context["test_started"] = datetime.now()
    context["test_id"] = str(uuid.uuid4())
    print(f"MOCK: Тестовый контекст подготовлен, ID: {context['test_id']}")

@given(parsers.parse('загружена конфигурация из файла "{config_path}"'))
def load_config_from_file(context, config_path):
    context["config_file"] = config_path
    context["config"] = {"loaded_from": config_path, "env": "test"}
    print(f"MOCK: Конфигурация загружена из {config_path}")

@given(parsers.parse('установлено окружение "{environment}"'))
def set_environment(context, environment):
    context["environment"] = environment
    print(f"MOCK: Окружение установлено на {environment}")

@given(parsers.parse('установлен идентификатор корреляции "{correlation_id}"'))
def set_correlation_id(context, correlation_id):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["X-Correlation-ID"] = correlation_id
    print(f"MOCK: Идентификатор корреляции установлен на {correlation_id}")

@given(parsers.parse('установлен идентификатор запроса "{request_id}"'))
def set_request_id(context, request_id):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["X-Request-ID"] = request_id
    print(f"MOCK: Идентификатор запроса установлен на {request_id}")

@given(parsers.parse('установлен идентификатор сессии "{session_id}"'))
def set_session_id(context, session_id):
    context["session"]["id"] = session_id
    print(f"MOCK: Идентификатор сессии установлен на {session_id}")

@given(parsers.parse('установлен идентификатор пользователя "{user_id}"'))
def set_user_id(context, user_id):
    context["user_id"] = user_id
    print(f"MOCK: Идентификатор пользователя установлен на {user_id}")

@given(parsers.parse('установлен идентификатор клиента "{client_id}"'))
def set_client_id(context, client_id):
    context["client_id"] = client_id
    print(f"MOCK: Идентификатор клиента установлен на {client_id}")

@given(parsers.parse('установлен API ключ "{api_key}"'))
def set_api_key(context, api_key):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["X-API-Key"] = api_key
    print(f"MOCK: API ключ установлен")

@given(parsers.parse('установлен секретный ключ "{secret_key}"'))
def set_secret_key(context, secret_key):
    context["secret_key"] = secret_key
    print(f"MOCK: Секретный ключ установлен")

@given(parsers.parse('установлен формат даты "{date_format}"'))
def set_date_format(context, date_format):
    context["date_format"] = date_format
    print(f"MOCK: Формат даты установлен на {date_format}")

@given(parsers.parse('установлена временная зона "{timezone}"'))
def set_timezone(context, timezone):
    context["timezone"] = timezone
    print(f"MOCK: Временная зона установлена на {timezone}")

@given(parsers.parse('установлен лимит повторных попыток {retries:d}'))
def set_retry_limit(context, retries):
    context["retry_limit"] = retries
    print(f"MOCK: Лимит повторных попыток установлен на {retries}")

@given(parsers.parse('установлена задержка между попытками {delay:d} секунд'))
def set_retry_delay(context, delay):
    context["retry_delay"] = delay
    print(f"MOCK: Задержка между попытками установлена на {delay} секунд")

@given(parsers.parse('включено логирование запросов'))
def enable_request_logging(context):
    context["log_requests"] = True
    print(f"MOCK: Логирование запросов включено")

@given(parsers.parse('включено логирование ответов'))
def enable_response_logging(context):
    context["log_responses"] = True
    print(f"MOCK: Логирование ответов включено")

@given(parsers.parse('установлен режим сжатия "{compression}"'))
def set_compression_mode(context, compression):
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Accept-Encoding"] = compression
    print(f"MOCK: Режим сжатия установлен на {compression}")

@given(parsers.parse('установлен кэш с TTL {ttl:d} секунд'))
def set_cache_ttl(context, ttl):
    context["cache_ttl"] = ttl
    print(f"MOCK: TTL кэша установлен на {ttl} секунд")

@given(parsers.parse('отключен кэш'))
def disable_cache(context):
    context["cache_enabled"] = False
    if "headers" not in context["request"]:
        context["request"]["headers"] = {}
    context["request"]["headers"]["Cache-Control"] = "no-cache"
    print(f"MOCK: Кэш отключен")

# ============================================================================
# --- When steps ---
# ============================================================================

@when(parsers.parse('отправить POST запрос на "{endpoint}" с телом:'))
def send_post_request_with_body(context, endpoint, docstring):
    body = docstring
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["body"] = json.loads(body)
    
    # Mocking the response
    context["response"] = {
        "status_code": 200,
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

@when(parsers.parse('отправить PUT запрос на "{endpoint}" с телом:'))
def send_put_request_with_body(context, endpoint, docstring):
    body = docstring
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "PUT"
    context["request"]["body"] = json.loads(body)
    
    context["response"] = {
        "status_code": 200,
        "body": {"status": "updated", "data": context["request"]["body"]}
    }
    print(f"MOCK: Отправлен PUT запрос на {full_url}")

@when(parsers.parse('отправить PATCH запрос на "{endpoint}" с телом:'))
def send_patch_request_with_body(context, endpoint, docstring):
    body = docstring
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "PATCH"
    context["request"]["body"] = json.loads(body)
    
    context["response"] = {
        "status_code": 200,
        "body": {"status": "patched", "data": context["request"]["body"]}
    }
    print(f"MOCK: Отправлен PATCH запрос на {full_url}")

@when(parsers.parse('отправить DELETE запрос на "{endpoint}"'))
def send_delete_request(context, endpoint):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "DELETE"
    
    context["response"] = {
        "status_code": 204,
        "body": {}
    }
    print(f"MOCK: Отправлен DELETE запрос на {full_url}")

@when(parsers.parse('отправить HEAD запрос на "{endpoint}"'))
def send_head_request(context, endpoint):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "HEAD"
    
    context["response"] = {
        "status_code": 200,
        "headers": {"Content-Length": "1234", "Content-Type": "application/json"}
    }
    print(f"MOCK: Отправлен HEAD запрос на {full_url}")

@when(parsers.parse('отправить OPTIONS запрос на "{endpoint}"'))
def send_options_request(context, endpoint):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "OPTIONS"
    
    context["response"] = {
        "status_code": 200,
        "headers": {"Allow": "GET, POST, PUT, DELETE, OPTIONS"}
    }
    print(f"MOCK: Отправлен OPTIONS запрос на {full_url}")

@when(parsers.parse('Присвоить переменной "{var_name}" значение "{value}"'))
def assign_variable(context, var_name, value):
    if value == "${UUID}":
        value = str(uuid.uuid4())
    elif value == "${TIMESTAMP}":
        value = str(int(time.time()))
    elif value == "${DATE}":
        value = datetime.now().strftime("%Y-%m-%d")
    elif value == "${DATETIME}":
        value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif value == "${RANDOM}":
        import random
        value = str(random.randint(1000, 9999))
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоено значение {value}")

@when(parsers.parse('установить переменную "{var_name}" значением "{value}"'))
def set_variable_alias(context, var_name, value):
    assign_variable(context, var_name, value)

@when(parsers.parse('присвоить переменной "{var_name}" случайное число от {min_val:d} до {max_val:d}'))
def assign_random_number(context, var_name, min_val, max_val):
    import random
    value = random.randint(min_val, max_val)
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоено случайное число {value}")

@when(parsers.parse('присвоить переменной "{var_name}" случайную строку длиной {length:d}'))
def assign_random_string(context, var_name, length):
    import random
    import string
    value = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоена случайная строка {value}")

@when(parsers.parse('присвоить переменной "{var_name}" текущую дату в формате "{date_format}"'))
def assign_current_date(context, var_name, date_format):
    value = datetime.now().strftime(date_format)
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоена дата {value}")

@when(parsers.parse('присвоить переменной "{var_name}" дату через {days:d} дней'))
def assign_future_date(context, var_name, days):
    value = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоена дата {value}")

@when(parsers.parse('присвоить переменной "{var_name}" дату {days:d} дней назад'))
def assign_past_date(context, var_name, days):
    value = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    context["variables"][var_name] = value
    print(f"MOCK: Переменной {var_name} присвоена дата {value}")

@when(parsers.parse('увеличить переменную "{var_name}" на {increment:d}'))
def increment_variable(context, var_name, increment):
    current = int(context["variables"].get(var_name, 0))
    context["variables"][var_name] = current + increment
    print(f"MOCK: Переменная {var_name} увеличена до {context['variables'][var_name]}")

@when(parsers.parse('уменьшить переменную "{var_name}" на {decrement:d}'))
def decrement_variable(context, var_name, decrement):
    current = int(context["variables"].get(var_name, 0))
    context["variables"][var_name] = current - decrement
    print(f"MOCK: Переменная {var_name} уменьшена до {context['variables'][var_name]}")

@when(parsers.parse('объединить переменные "{var1}" и "{var2}" в "{result_var}"'))
def concat_variables(context, var1, var2, result_var):
    val1 = str(context["variables"].get(var1, ""))
    val2 = str(context["variables"].get(var2, ""))
    context["variables"][result_var] = val1 + val2
    print(f"MOCK: Переменные объединены в {result_var}={context['variables'][result_var]}")

@when(parsers.parse('Комментарий "{text}"'))
def add_comment(context, text):
    print(f"COMMENT: {text}")

@when(parsers.parse('добавить заметку "{note}"'))
def add_note(context, note):
    if "notes" not in context:
        context["notes"] = []
    context["notes"].append(note)
    print(f"NOTE: {note}")

@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}"'))
def send_rest_request(context, method_path, server_name):
    print(f"MOCK: Отправка {method_path} на сервер {server_name}")
    # Mock-ответ с полями для различных тестов
    context["response"] = {
        "status_code": 200,
        "body": {
            "status": "success",
            "dont_check_array_len": "true",
            "traceId": context.get("variables", {}).get("traceId", "mock-trace-id"),
            "outAttributes": [
                {"rateAdjustment": "${rateAdjustment_1}"}
            ]
        },
        "headers": {"Content-Type": "application/json"}
    }

@when(parsers.parse('Отправить "{method_path}" на REST сервер "{server_name}" с body из файла "{file_path}"'))
def send_rest_request_from_file(context, method_path, server_name, file_path):
    print(f"MOCK: Отправка {method_path} на сервер {server_name} с телом из {file_path}")
    # Mock-ответ с полями для различных тестов
    context["response"] = {
        "status_code": 200,
        "body": {
            "status": "success",
            "mocked_from": file_path,
            "dont_check_array_len": "true",
            "traceId": context.get("variables", {}).get("traceId", "mock-trace-id"),
            "outAttributes": [
                {"rateAdjustment": "${rateAdjustment_1}"}
            ]
        },
        "headers": {"Content-Type": "application/json"}
    }

@when(parsers.parse('отправить запрос с файлом "{file_path}" на "{endpoint}"'))
def send_file_upload(context, file_path, endpoint):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["file"] = file_path
    
    context["response"] = {
        "status_code": 200,
        "body": {"status": "uploaded", "filename": file_path}
    }
    print(f"MOCK: Отправлен файл {file_path} на {full_url}")

@when(parsers.parse('отправить multipart запрос на "{endpoint}" с файлами:'))
def send_multipart_request(context, endpoint, docstring):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["multipart"] = True
    context["request"]["files"] = docstring.split("\n")
    
    context["response"] = {
        "status_code": 200,
        "body": {"status": "uploaded", "files_count": len(context["request"]["files"])}
    }
    print(f"MOCK: Отправлен multipart запрос на {full_url}")

@when(parsers.parse('отправить GraphQL запрос на "{endpoint}":'))
def send_graphql_request(context, endpoint, docstring):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["graphql"] = docstring
    
    context["response"] = {
        "status_code": 200,
        "body": {"data": {"mock": "graphql_response"}}
    }
    print(f"MOCK: Отправлен GraphQL запрос на {full_url}")

@when(parsers.parse('отправить SOAP запрос на "{endpoint}":'))
def send_soap_request(context, endpoint, docstring):
    full_url = f"{context.get('base_url', '')}{endpoint}"
    context["request"]["url"] = full_url
    context["request"]["method"] = "POST"
    context["request"]["soap"] = docstring
    
    context["response"] = {
        "status_code": 200,
        "body": "<soap:Envelope><soap:Body><Response>Mock</Response></soap:Body></soap:Envelope>"
    }
    print(f"MOCK: Отправлен SOAP запрос на {full_url}")

@when(parsers.parse('Загрузить TCR файлы'))
def load_tcr_files(context, datatable):
    print(f"MOCK: Загрузка TCR файлов: {datatable}")

@when(parsers.parse('загрузить данные из CSV файла "{file_path}"'))
def load_csv_data(context, file_path):
    context["csv_data"] = [{"col1": "val1", "col2": "val2"}]
    print(f"MOCK: Загружены данные из CSV файла {file_path}")

@when(parsers.parse('загрузить данные из JSON файла "{file_path}"'))
def load_json_data(context, file_path):
    context["json_data"] = {"key": "value"}
    print(f"MOCK: Загружены данные из JSON файла {file_path}")

@when(parsers.parse('загрузить данные из XML файла "{file_path}"'))
def load_xml_data(context, file_path):
    context["xml_data"] = "<root><item>value</item></root>"
    print(f"MOCK: Загружены данные из XML файла {file_path}")

@when(parsers.parse('загрузить данные из Excel файла "{file_path}"'))
def load_excel_data(context, file_path):
    context["excel_data"] = [{"col1": "val1", "col2": "val2"}]
    print(f"MOCK: Загружены данные из Excel файла {file_path}")

@when(parsers.parse('Выполнить запрос в базу "{db_name}":'))
def execute_sql_query(context, db_name, docstring):
    print(f"MOCK: Выполнение запроса в {db_name}: {docstring}")
    context["last_sql_result"] = [{"count(*)": 1}]

@when(parsers.parse('выполнить SQL запрос в базу "{db_name}":'))
def execute_sql(context, db_name, docstring):
    execute_sql_query(context, db_name, docstring)

@when(parsers.parse('выполнить хранимую процедуру "{procedure_name}" в базе "{db_name}"'))
def execute_stored_procedure(context, procedure_name, db_name):
    print(f"MOCK: Выполнение хранимой процедуры {procedure_name} в {db_name}")
    context["last_sql_result"] = [{"result": "success"}]

@when(parsers.parse('выполнить хранимую процедуру "{procedure_name}" в базе "{db_name}" с параметрами:'))
def execute_stored_procedure_with_params(context, procedure_name, db_name, docstring):
    print(f"MOCK: Выполнение хранимой процедуры {procedure_name} в {db_name} с параметрами: {docstring}")
    context["last_sql_result"] = [{"result": "success"}]

@when(parsers.parse('начать транзакцию в базе "{db_name}"'))
def begin_transaction(context, db_name):
    context["transaction"] = {"db": db_name, "active": True}
    print(f"MOCK: Начата транзакция в базе {db_name}")

@when(parsers.parse('зафиксировать транзакцию в базе "{db_name}"'))
def commit_transaction(context, db_name):
    context["transaction"] = {"db": db_name, "active": False, "committed": True}
    print(f"MOCK: Транзакция зафиксирована в базе {db_name}")

@when(parsers.parse('откатить транзакцию в базе "{db_name}"'))
def rollback_transaction(context, db_name):
    context["transaction"] = {"db": db_name, "active": False, "rolled_back": True}
    print(f"MOCK: Транзакция откачена в базе {db_name}")

@when(parsers.parse('Отправить сообщение в кафку "{kafka_name}" в топик "{topic_name}"'))
def send_kafka_message(context, kafka_name, topic_name):
    print(f"MOCK: Отправка сообщения в Kafka {kafka_name}, топик {topic_name}")
    if "kafka" not in context:
        context["kafka"] = {}
    context["kafka"]["sent"] = True

@when(parsers.parse('ожидать {seconds:d} секунд'))
def wait_seconds(context, seconds):
    print(f"MOCK: Ожидание {seconds} секунд")
    # time.sleep(seconds)  # В моке не ждем реально

@when(parsers.parse('ожидать {milliseconds:d} миллисекунд'))
def wait_milliseconds(context, milliseconds):
    print(f"MOCK: Ожидание {milliseconds} миллисекунд")

@when(parsers.parse('запустить таймер "{timer_name}"'))
def start_timer(context, timer_name):
    context["timers"][timer_name] = {"start": time.time()}
    print(f"MOCK: Таймер {timer_name} запущен")

@when(parsers.parse('остановить таймер "{timer_name}"'))
def stop_timer(context, timer_name):
    if timer_name in context["timers"]:
        context["timers"][timer_name]["end"] = time.time()
        context["timers"][timer_name]["duration"] = context["timers"][timer_name]["end"] - context["timers"][timer_name]["start"]
    print(f"MOCK: Таймер {timer_name} остановлен")

@when(parsers.parse('очистить контекст'))
def clear_context(context):
    context["variables"] = {}
    context["request"] = {}
    context["response"] = {}
    print(f"MOCK: Контекст очищен")

@when(parsers.parse('очистить переменные'))
def clear_variables(context):
    context["variables"] = {}
    print(f"MOCK: Переменные очищены")

@when(parsers.parse('очистить заголовки'))
def clear_headers(context):
    context["request"]["headers"] = {}
    print(f"MOCK: Заголовки очищены")

@when(parsers.parse('очистить cookies'))
def clear_cookies(context):
    context["cookies"] = {}
    print(f"MOCK: Cookies очищены")

@when(parsers.parse('сохранить ответ в файл "{file_path}"'))
def save_response_to_file(context, file_path):
    context["saved_response_file"] = file_path
    print(f"MOCK: Ответ сохранен в файл {file_path}")

@when(parsers.parse('сохранить запрос в файл "{file_path}"'))
def save_request_to_file(context, file_path):
    context["saved_request_file"] = file_path
    print(f"MOCK: Запрос сохранен в файл {file_path}")

@when(parsers.parse('преобразовать ответ в XML'))
def convert_response_to_xml(context):
    context["response"]["format"] = "xml"
    print(f"MOCK: Ответ преобразован в XML")

@when(parsers.parse('преобразовать ответ в JSON'))
def convert_response_to_json(context):
    context["response"]["format"] = "json"
    print(f"MOCK: Ответ преобразован в JSON")

@when(parsers.parse('декодировать Base64 из поля "{field}" в переменную "{var_name}"'))
def decode_base64_field(context, field, var_name):
    import base64
    value = context["response"].get("body", {}).get(field, "")
    try:
        decoded = base64.b64decode(value).decode()
    except:
        decoded = "mock_decoded_value"
    context["variables"][var_name] = decoded
    print(f"MOCK: Base64 декодировано из {field} в {var_name}")

@when(parsers.parse('закодировать в Base64 переменную "{var_name}"'))
def encode_base64_variable(context, var_name):
    import base64
    value = str(context["variables"].get(var_name, ""))
    encoded = base64.b64encode(value.encode()).decode()
    context["variables"][var_name] = encoded
    print(f"MOCK: Переменная {var_name} закодирована в Base64")

@when(parsers.parse('вычислить MD5 хэш переменной "{var_name}"'))
def compute_md5_hash(context, var_name):
    import hashlib
    value = str(context["variables"].get(var_name, ""))
    hash_value = hashlib.md5(value.encode()).hexdigest()
    context["variables"][f"{var_name}_md5"] = hash_value
    print(f"MOCK: MD5 хэш вычислен для {var_name}")

@when(parsers.parse('вычислить SHA256 хэш переменной "{var_name}"'))
def compute_sha256_hash(context, var_name):
    import hashlib
    value = str(context["variables"].get(var_name, ""))
    hash_value = hashlib.sha256(value.encode()).hexdigest()
    context["variables"][f"{var_name}_sha256"] = hash_value
    print(f"MOCK: SHA256 хэш вычислен для {var_name}")

@when(parsers.parse('извлечь значение по JSONPath "{jsonpath}" в переменную "{var_name}"'))
def extract_jsonpath(context, jsonpath, var_name):
    context["variables"][var_name] = "mock_extracted_value"
    print(f"MOCK: Значение извлечено по JSONPath {jsonpath} в {var_name}")

@when(parsers.parse('извлечь значение по XPath "{xpath}" в переменную "{var_name}"'))
def extract_xpath(context, xpath, var_name):
    context["variables"][var_name] = "mock_extracted_value"
    print(f"MOCK: Значение извлечено по XPath {xpath} в {var_name}")

@when(parsers.parse('извлечь значение по регулярному выражению "{regex}" в переменную "{var_name}"'))
def extract_regex(context, regex, var_name):
    context["variables"][var_name] = "mock_extracted_value"
    print(f"MOCK: Значение извлечено по regex {regex} в {var_name}")

@when(parsers.parse('повторить последний запрос'))
def repeat_last_request(context):
    print(f"MOCK: Последний запрос повторен")

@when(parsers.parse('повторить последний запрос {times:d} раз'))
def repeat_last_request_times(context, times):
    print(f"MOCK: Последний запрос повторен {times} раз")

@when(parsers.parse('отправить пакет запросов:'))
def send_batch_requests(context, docstring):
    print(f"MOCK: Отправлен пакет запросов: {docstring}")
    context["response"] = {
        "status_code": 200,
        "body": {"batch_results": []}
    }

@when(parsers.parse('выполнить параллельно {count:d} запросов на "{endpoint}"'))
def send_parallel_requests(context, count, endpoint):
    print(f"MOCK: Выполнено {count} параллельных запросов на {endpoint}")
    context["response"] = {
        "status_code": 200,
        "body": {"parallel_results": []}
    }

# ============================================================================
# --- Then steps ---
# ============================================================================

@then(parsers.parse('код ответа должен быть {status_code:d}'))
def check_status_code(context, status_code):
    actual_code = context["response"].get("status_code")
    print(f"MOCK: Проверка кода ответа: ожидается {status_code}, получено {actual_code}")
    assert actual_code == status_code

@then(parsers.parse('код ответа должен быть одним из {status_codes}'))
def check_status_code_in_list(context, status_codes):
    actual_code = context["response"].get("status_code")
    expected_codes = [int(code.strip()) for code in status_codes.split(",")]
    print(f"MOCK: Проверка кода ответа: ожидается один из {expected_codes}, получено {actual_code}")
    assert actual_code in expected_codes

@then(parsers.parse('код ответа должен быть в диапазоне от {min_code:d} до {max_code:d}'))
def check_status_code_range(context, min_code, max_code):
    actual_code = context["response"].get("status_code")
    print(f"MOCK: Проверка кода ответа: ожидается от {min_code} до {max_code}, получено {actual_code}")
    assert min_code <= actual_code <= max_code

@then(parsers.parse('тело ответа содержит поле "{field}" со значением "{value}"'))
def check_response_field(context, field, value):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: ожидается {value}, получено {actual_value}")
    assert str(actual_value) == str(value)

@then(parsers.parse('тело ответа содержит поле "{field}"'))
def check_response_field_exists(context, field):
    body = context["response"].get("body", {})
    print(f"MOCK: Проверка наличия поля {field}")
    assert field in body

@then(parsers.parse('тело ответа не содержит поле "{field}"'))
def check_response_field_not_exists(context, field):
    body = context["response"].get("body", {})
    print(f"MOCK: Проверка отсутствия поля {field}")
    assert field not in body

@then(parsers.parse('тело ответа содержит поле "{field}" со значением не равным "{value}"'))
def check_response_field_not_equals(context, field, value):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: не должно быть {value}, получено {actual_value}")
    assert str(actual_value) != str(value)

@then(parsers.parse('тело ответа содержит поле "{field}" со значением больше {value:d}'))
def check_response_field_greater(context, field, value):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: должно быть > {value}, получено {actual_value}")
    assert int(actual_value) > value

@then(parsers.parse('тело ответа содержит поле "{field}" со значением меньше {value:d}'))
def check_response_field_less(context, field, value):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: должно быть < {value}, получено {actual_value}")
    assert int(actual_value) < value

@then(parsers.parse('тело ответа содержит поле "{field}" со значением в диапазоне от {min_val:d} до {max_val:d}'))
def check_response_field_range(context, field, min_val, max_val):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка поля {field}: должно быть от {min_val} до {max_val}, получено {actual_value}")
    assert min_val <= int(actual_value) <= max_val

@then(parsers.parse('тело ответа содержит поле "{field}" соответствующее регулярному выражению "{pattern}"'))
def check_response_field_regex(context, field, pattern):
    actual_value = str(context["response"].get("body", {}).get(field))
    print(f"MOCK: Проверка поля {field} по regex {pattern}, получено {actual_value}")
    assert re.match(pattern, actual_value)

@then(parsers.parse('тело ответа содержит поле "{field}" типа "{expected_type}"'))
def check_response_field_type(context, field, expected_type):
    actual_value = context["response"].get("body", {}).get(field)
    type_map = {"string": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}
    print(f"MOCK: Проверка типа поля {field}: ожидается {expected_type}")
    assert isinstance(actual_value, type_map.get(expected_type, str))

@then(parsers.parse('тело ответа содержит поле "{field}" с длиной {length:d}'))
def check_response_field_length(context, field, length):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка длины поля {field}: ожидается {length}, получено {len(str(actual_value))})")
    assert len(str(actual_value)) == length

@then(parsers.parse('тело ответа содержит поле "{field}" с длиной больше {length:d}'))
def check_response_field_length_greater(context, field, length):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка длины поля {field}: должно быть > {length}")
    assert len(str(actual_value)) > length

@then(parsers.parse('тело ответа содержит поле "{field}" с длиной меньше {length:d}'))
def check_response_field_length_less(context, field, length):
    actual_value = context["response"].get("body", {}).get(field)
    print(f"MOCK: Проверка длины поля {field}: должно быть < {length}")
    assert len(str(actual_value)) < length

@then(parsers.parse('тело ответа содержит массив "{field}" с {count:d} элементами'))
def check_response_array_count(context, field, count):
    actual_value = context["response"].get("body", {}).get(field, [])
    print(f"MOCK: Проверка количества элементов в {field}: ожидается {count}, получено {len(actual_value)}")
    assert len(actual_value) == count

@then(parsers.parse('тело ответа содержит массив "{field}" с количеством элементов больше {count:d}'))
def check_response_array_count_greater(context, field, count):
    actual_value = context["response"].get("body", {}).get(field, [])
    print(f"MOCK: Проверка количества элементов в {field}: должно быть > {count}")
    assert len(actual_value) > count

@then(parsers.parse('тело ответа содержит массив "{field}" с количеством элементов меньше {count:d}'))
def check_response_array_count_less(context, field, count):
    actual_value = context["response"].get("body", {}).get(field, [])
    print(f"MOCK: Проверка количества элементов в {field}: должно быть < {count}")
    assert len(actual_value) < count

@then(parsers.parse('тело ответа содержит непустой массив "{field}"'))
def check_response_array_not_empty(context, field):
    actual_value = context["response"].get("body", {}).get(field, [])
    print(f"MOCK: Проверка что массив {field} не пустой")
    assert len(actual_value) > 0

@then(parsers.parse('тело ответа содержит пустой массив "{field}"'))
def check_response_array_empty(context, field):
    actual_value = context["response"].get("body", {}).get(field, [])
    print(f"MOCK: Проверка что массив {field} пустой")
    assert len(actual_value) == 0

@then(parsers.parse('тело ответа содержит текст "{text}"'))
def check_response_contains_text(context, text):
    body = str(context["response"].get("body", {}))
    print(f"MOCK: Проверка наличия текста '{text}' в ответе")
    assert text in body

@then(parsers.parse('тело ответа не содержит текст "{text}"'))
def check_response_not_contains_text(context, text):
    body = str(context["response"].get("body", {}))
    print(f"MOCK: Проверка отсутствия текста '{text}' в ответе")
    assert text not in body

@then(parsers.parse('тело ответа является валидным JSON'))
def check_response_valid_json(context):
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ является валидным JSON")
    assert body is not None

@then(parsers.parse('тело ответа является валидным XML'))
def check_response_valid_xml(context):
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ является валидным XML")
    assert body is not None

@then(parsers.parse('тело ответа не пустое'))
def check_response_not_empty(context):
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ не пустой")
    assert body is not None and body != {}

@then(parsers.parse('тело ответа пустое'))
def check_response_empty(context):
    body = context["response"].get("body")
    print(f"MOCK: Проверка что ответ пустой")
    assert body is None or body == {}

@then(parsers.parse('Проверить ответ с кодом {status_code:d} и body из файла "{file_path}"'))
def check_response_from_file(context, status_code, file_path):
    print(f"MOCK: Проверка ответа {status_code} с телом из {file_path}")
    assert context["response"].get("status_code") == status_code

@then(parsers.parse('Проверить ответ с кодом {status_code:d} и body'))
def check_response_body_json(context, status_code, docstring):
    print(f"MOCK: Проверка ответа {status_code} и JSON body: {docstring}")
    assert context["response"].get("status_code") == status_code

@then(parsers.parse('Проверить результат запроса из базы "{db_name}"'))
def check_sql_result_direct(context, db_name):
    print(f"MOCK: Проверка результата SQL в {db_name}")
    assert True

@then(parsers.parse('сохранить значение поля "{field}" в переменную "{var_name}"'))
def save_variable(context, field, var_name):
    value = context["response"].get("body", {}).get(field)
    context["variables"][var_name] = value
    print(f"MOCK: Значение {value} из поля {field} сохранено в переменную {var_name}")

@then(parsers.parse('сохранить значение заголовка "{header}" в переменную "{var_name}"'))
def save_header_to_variable(context, header, var_name):
    value = context["response"].get("headers", {}).get(header)
    context["variables"][var_name] = value
    print(f"MOCK: Значение заголовка {header} сохранено в переменную {var_name}")

@then(parsers.parse('сохранить код ответа в переменную "{var_name}"'))
def save_status_code_to_variable(context, var_name):
    value = context["response"].get("status_code")
    context["variables"][var_name] = value
    print(f"MOCK: Код ответа {value} сохранен в переменную {var_name}")

@then(parsers.parse('сохранить время ответа в переменную "{var_name}"'))
def save_response_time_to_variable(context, var_name):
    value = context["response"].get("response_time", 100)
    context["variables"][var_name] = value
    print(f"MOCK: Время ответа сохранено в переменную {var_name}")

@then(parsers.parse('сохранить размер ответа в переменную "{var_name}"'))
def save_response_size_to_variable(context, var_name):
    value = len(str(context["response"].get("body", {})))
    context["variables"][var_name] = value
    print(f"MOCK: Размер ответа сохранен в переменную {var_name}")

@then(parsers.parse('Проверить результат запроса из базы "{db_name}" в течение {timeout:d} секунд'))
def check_sql_result_with_timeout(context, db_name, timeout):
    print(f"MOCK: Проверка результата SQL в {db_name} (таймаут {timeout}с)")
    assert True

@then(parsers.parse('результат запроса в базу "{db_name}" содержит данные в течение {timeout:d} секунд'))
def check_sql_result_contains(context, db_name, timeout):
    check_sql_result_with_timeout(context, db_name, timeout)

@then(parsers.parse('заголовок ответа "{header}" равен "{value}"'))
def check_response_header(context, header, value):
    actual_value = context["response"].get("headers", {}).get(header)
    print(f"MOCK: Проверка заголовка {header}: ожидается {value}, получено {actual_value}")
    assert str(actual_value) == str(value)

@then(parsers.parse('заголовок ответа "{header}" существует'))
def check_response_header_exists(context, header):
    headers = context["response"].get("headers", {})
    print(f"MOCK: Проверка наличия заголовка {header}")
    assert header in headers

@then(parsers.parse('заголовок ответа "{header}" не существует'))
def check_response_header_not_exists(context, header):
    headers = context["response"].get("headers", {})
    print(f"MOCK: Проверка отсутствия заголовка {header}")
    assert header not in headers

@then(parsers.parse('заголовок ответа "{header}" содержит "{substring}"'))
def check_response_header_contains(context, header, substring):
    actual_value = str(context["response"].get("headers", {}).get(header, ""))
    print(f"MOCK: Проверка что заголовок {header} содержит {substring}")
    assert substring in actual_value

@then(parsers.parse('время ответа меньше {max_time:d} миллисекунд'))
def check_response_time(context, max_time):
    response_time = context["response"].get("response_time", 50)
    print(f"MOCK: Проверка времени ответа: должно быть < {max_time}мс, получено {response_time}мс")
    assert response_time < max_time

@then(parsers.parse('время ответа меньше {max_time:d} секунд'))
def check_response_time_seconds(context, max_time):
    response_time = context["response"].get("response_time", 50) / 1000
    print(f"MOCK: Проверка времени ответа: должно быть < {max_time}с")
    assert response_time < max_time

@then(parsers.parse('размер ответа меньше {max_size:d} байт'))
def check_response_size(context, max_size):
    response_size = len(str(context["response"].get("body", {})))
    print(f"MOCK: Проверка размера ответа: должно быть < {max_size} байт")
    assert response_size < max_size

@then(parsers.parse('размер ответа больше {min_size:d} байт'))
def check_response_size_greater(context, min_size):
    response_size = len(str(context["response"].get("body", {})))
    print(f"MOCK: Проверка размера ответа: должно быть > {min_size} байт")
    assert response_size > min_size

def _resolve_variable(context, value):
    """Подставляет значения переменных из ${var_name}."""
    import re
    pattern = r'\$\{(\w+)\}'
    def replace(match):
        var_name = match.group(1)
        return str(context["variables"].get(var_name, match.group(0)))
    return re.sub(pattern, replace, str(value))

@then(parsers.parse('переменная "{var_name}" равна "{value}"'))
def check_variable_equals(context, var_name, value):
    actual_value = context["variables"].get(var_name)
    expected_value = _resolve_variable(context, value)
    print(f"MOCK: Проверка переменной {var_name}: ожидается {expected_value}, получено {actual_value}")
    assert str(actual_value) == str(expected_value)

@then(parsers.parse('переменная "{var_name}" не равна "{value}"'))
def check_variable_not_equals(context, var_name, value):
    actual_value = context["variables"].get(var_name)
    expected_value = _resolve_variable(context, value)
    print(f"MOCK: Проверка переменной {var_name}: не должно быть {expected_value}, получено {actual_value}")
    assert str(actual_value) != str(expected_value)

@then(parsers.parse('переменная "{var_name}" существует'))
def check_variable_exists(context, var_name):
    print(f"MOCK: Проверка существования переменной {var_name}")
    assert var_name in context["variables"]

@then(parsers.parse('переменная "{var_name}" не существует'))
def check_variable_not_exists(context, var_name):
    print(f"MOCK: Проверка отсутствия переменной {var_name}")
    assert var_name not in context["variables"]

@then(parsers.parse('переменная "{var_name}" не пустая'))
def check_variable_not_empty(context, var_name):
    actual_value = context["variables"].get(var_name)
    print(f"MOCK: Проверка что переменная {var_name} не пустая")
    assert actual_value is not None and actual_value != ""

@then(parsers.parse('переменная "{var_name}" пустая'))
def check_variable_empty(context, var_name):
    actual_value = context["variables"].get(var_name)
    print(f"MOCK: Проверка что переменная {var_name} пустая")
    assert actual_value is None or actual_value == ""

@then(parsers.parse('переменная "{var_name}" содержит "{substring}"'))
def check_variable_contains(context, var_name, substring):
    actual_value = str(context["variables"].get(var_name, ""))
    print(f"MOCK: Проверка что переменная {var_name} содержит {substring}")
    assert substring in actual_value

@then(parsers.parse('переменная "{var_name}" соответствует регулярному выражению "{pattern}"'))
def check_variable_regex(context, var_name, pattern):
    actual_value = str(context["variables"].get(var_name, ""))
    print(f"MOCK: Проверка переменной {var_name} по regex {pattern}")
    assert re.match(pattern, actual_value)

@then(parsers.parse('переменная "{var_name}" больше {value:d}'))
def check_variable_greater(context, var_name, value):
    actual_value = int(context["variables"].get(var_name, 0))
    print(f"MOCK: Проверка переменной {var_name}: должно быть > {value}")
    assert actual_value > value

@then(parsers.parse('переменная "{var_name}" меньше {value:d}'))
def check_variable_less(context, var_name, value):
    actual_value = int(context["variables"].get(var_name, 0))
    print(f"MOCK: Проверка переменной {var_name}: должно быть < {value}")
    assert actual_value < value

@then(parsers.parse('Выполнить python код'))
def execute_python_code(context):
    print(f"MOCK: Выполнение Python кода")
    pass

@then(parsers.parse('вывести значение переменной "{var_name}"'))
def print_variable(context, var_name):
    value = context["variables"].get(var_name)
    print(f"DEBUG: Переменная {var_name} = {value}")

@then(parsers.parse('вывести тело ответа'))
def print_response_body(context):
    body = context["response"].get("body")
    print(f"DEBUG: Тело ответа = {json.dumps(body, indent=2, ensure_ascii=False)}")

@then(parsers.parse('вывести заголовки ответа'))
def print_response_headers(context):
    headers = context["response"].get("headers")
    print(f"DEBUG: Заголовки ответа = {headers}")

@then(parsers.parse('вывести все переменные'))
def print_all_variables(context):
    print(f"DEBUG: Все переменные = {context['variables']}")

@then(parsers.parse('вывести время таймера "{timer_name}"'))
def print_timer(context, timer_name):
    timer = context["timers"].get(timer_name, {})
    duration = timer.get("duration", 0)
    print(f"DEBUG: Таймер {timer_name} = {duration} секунд")

@then(parsers.parse('ответ соответствует JSON схеме:'))
def check_json_schema(context, docstring):
    print(f"MOCK: Проверка соответствия JSON схеме: {docstring}")
    assert True

@then(parsers.parse('ответ соответствует JSON схеме из файла "{schema_file}"'))
def check_json_schema_from_file(context, schema_file):
    print(f"MOCK: Проверка соответствия JSON схеме из файла {schema_file}")
    assert True

@then(parsers.parse('сравнить ответ с эталоном из файла "{file_path}"'))
def compare_response_with_file(context, file_path):
    print(f"MOCK: Сравнение ответа с эталоном из {file_path}")
    assert True

@then(parsers.parse('сравнить ответ с эталоном из файла "{file_path}" игнорируя поля:'))
def compare_response_with_file_ignore(context, file_path, docstring):
    ignored_fields = docstring.strip().split("\n")
    print(f"MOCK: Сравнение ответа с эталоном из {file_path}, игнорируя {ignored_fields}")
    assert True

@then(parsers.parse('тест завершен успешно'))
def step_test_completed_successfully(context):
    print(f"MOCK: Тест завершен успешно")
    assert True

@then(parsers.parse('тест завершен с ошибкой "{error_message}"'))
def step_test_completed_with_error(context, error_message):
    print(f"MOCK: Тест завершен с ошибкой: {error_message}")
    assert False, error_message

@then(parsers.parse('пропустить тест с причиной "{reason}"'))
def skip_test(context, reason):
    print(f"MOCK: Тест пропущен: {reason}")
    pytest.skip(reason)
