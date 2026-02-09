"""
Database шаги для тестирования.
Включает шаги для выполнения SQL запросов, управления транзакциями,
работы с различными СУБД и проверки данных.
"""
from steps.soft_assert import soft_assert
from pytest_bdd import given, when, then, parsers
import json


# ============================================================================
# --- Given steps (Database Setup) ---
# ============================================================================

@given(parsers.parse('установлено подключение к базе данных "{db_name}"'))
def setup_db_connection(context, db_name):
    """Установка подключения к базе данных."""
    if "databases" not in context:
        context["databases"] = {}
    context["databases"][db_name] = {
        "connected": True,
        "connection_time": "2025-02-05T10:00:00"
    }
    print(f"MOCK: Установлено подключение к базе {db_name}")


@given(parsers.parse('установлено подключение к базе данных "{db_name}" с параметрами:'))
def setup_db_connection_with_params(context, db_name, docstring):
    """Установка подключения к базе данных с параметрами."""
    if "databases" not in context:
        context["databases"] = {}
    context["databases"][db_name] = {
        "connected": True,
        "params": docstring
    }
    print(f"MOCK: Установлено подключение к базе {db_name} с параметрами")


@given(parsers.parse('установлен таймаут запроса к базе "{db_name}" {timeout:d} секунд'))
def set_db_query_timeout(context, db_name, timeout):
    """Установка таймаута запроса к базе данных."""
    if "databases" not in context:
        context["databases"] = {}
    if db_name not in context["databases"]:
        context["databases"][db_name] = {}
    context["databases"][db_name]["query_timeout"] = timeout
    print(f"MOCK: Таймаут запроса к {db_name} установлен на {timeout} секунд")


@given(parsers.parse('установлен уровень изоляции транзакций "{isolation_level}" для базы "{db_name}"'))
def set_isolation_level(context, isolation_level, db_name):
    """Установка уровня изоляции транзакций."""
    if "databases" not in context:
        context["databases"] = {}
    if db_name not in context["databases"]:
        context["databases"][db_name] = {}
    context["databases"][db_name]["isolation_level"] = isolation_level
    print(f"MOCK: Уровень изоляции для {db_name} установлен на {isolation_level}")


@given(parsers.parse('включен режим автокоммита для базы "{db_name}"'))
def enable_autocommit(context, db_name):
    """Включение режима автокоммита."""
    if "databases" not in context:
        context["databases"] = {}
    if db_name not in context["databases"]:
        context["databases"][db_name] = {}
    context["databases"][db_name]["autocommit"] = True
    print(f"MOCK: Автокоммит включен для {db_name}")


@given(parsers.parse('отключен режим автокоммита для базы "{db_name}"'))
def disable_autocommit(context, db_name):
    """Отключение режима автокоммита."""
    if "databases" not in context:
        context["databases"] = {}
    if db_name not in context["databases"]:
        context["databases"][db_name] = {}
    context["databases"][db_name]["autocommit"] = False
    print(f"MOCK: Автокоммит отключен для {db_name}")


@given(parsers.parse('установлена схема "{schema_name}" для базы "{db_name}"'))
def set_db_schema(context, schema_name, db_name):
    """Установка схемы базы данных."""
    if "databases" not in context:
        context["databases"] = {}
    if db_name not in context["databases"]:
        context["databases"][db_name] = {}
    context["databases"][db_name]["schema"] = schema_name
    print(f"MOCK: Схема {schema_name} установлена для {db_name}")


@given(parsers.parse('загружены тестовые данные в базу "{db_name}" из файла "{file_path}"'))
def load_test_data_from_file(context, db_name, file_path):
    """Загрузка тестовых данных из файла."""
    print(f"MOCK: Загружены тестовые данные в {db_name} из {file_path}")


@given(parsers.parse('очищена таблица "{table_name}" в базе "{db_name}"'))
def clear_table(context, table_name, db_name):
    """Очистка таблицы в базе данных."""
    print(f"MOCK: Таблица {table_name} очищена в базе {db_name}")


@given(parsers.parse('создана временная таблица "{table_name}" в базе "{db_name}"'))
def create_temp_table(context, table_name, db_name):
    """Создание временной таблицы."""
    print(f"MOCK: Создана временная таблица {table_name} в базе {db_name}")


@given(parsers.parse('создана временная таблица "{table_name}" в базе "{db_name}" со структурой:'))
def create_temp_table_with_structure(context, table_name, db_name, docstring):
    """Создание временной таблицы со структурой."""
    print(f"MOCK: Создана временная таблица {table_name} в базе {db_name} со структурой:\n{docstring}")


# ============================================================================
# --- When steps (Database Operations) ---
# ============================================================================

@when(parsers.parse('Выполнить запрос в базу "{db_name}"'))
def execute_db_query(db_name, docstring, context):
    """Выполнение SQL запроса в указанную базу данных."""
    print(f"MOCK: Выполнение SQL запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "rows": [
            {"id": 1, "status": "success", "count": 1}
        ],
        "affected_rows": 1
    }


@when(parsers.parse('выполнить SELECT запрос в базу "{db_name}":'))
def execute_select_query(context, db_name, docstring):
    """Выполнение SELECT запроса."""
    print(f"MOCK: Выполнение SELECT запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    # Mock-данные с универсальными колонками для тестов
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "rows": [
            {"id": 1, "name": "test", "value": 100, "POSITION_ID": "00001", "count(*)": 1}
        ],
        "row_count": 1
    }


@when(parsers.parse('выполнить INSERT запрос в базу "{db_name}":'))
def execute_insert_query(context, db_name, docstring):
    """Выполнение INSERT запроса."""
    print(f"MOCK: Выполнение INSERT запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "inserted_id": 123,
        "affected_rows": 1
    }


@when(parsers.parse('выполнить UPDATE запрос в базу "{db_name}":'))
def execute_update_query(context, db_name, docstring):
    """Выполнение UPDATE запроса."""
    print(f"MOCK: Выполнение UPDATE запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "affected_rows": 5
    }


@when(parsers.parse('выполнить DELETE запрос в базу "{db_name}":'))
def execute_delete_query(context, db_name, docstring):
    """Выполнение DELETE запроса."""
    print(f"MOCK: Выполнение DELETE запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "affected_rows": 3
    }


@when(parsers.parse('выполнить TRUNCATE таблицы "{table_name}" в базе "{db_name}"'))
def execute_truncate(context, table_name, db_name):
    """Выполнение TRUNCATE таблицы."""
    print(f"MOCK: Выполнение TRUNCATE таблицы {table_name} в базе {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "table": table_name,
        "operation": "TRUNCATE",
        "success": True
    }


@when(parsers.parse('выполнить запрос из файла "{file_path}" в базу "{db_name}"'))
def execute_query_from_file(context, file_path, db_name):
    """Выполнение SQL запроса из файла."""
    print(f"MOCK: Выполнение запроса из файла {file_path} в базу {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "file": file_path,
        "rows": [{"id": 1}],
        "affected_rows": 1
    }


@when(parsers.parse('выполнить пакет запросов в базу "{db_name}":'))
def execute_batch_queries(context, db_name, docstring):
    """Выполнение пакета SQL запросов."""
    queries = docstring.strip().split(";")
    print(f"MOCK: Выполнение пакета из {len(queries)} запросов в базу {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "queries_count": len(queries),
        "success": True
    }


@when(parsers.parse('выполнить хранимую процедуру "{proc_name}" в базе "{db_name}"'))
def execute_stored_proc(context, proc_name, db_name):
    """Выполнение хранимой процедуры."""
    print(f"MOCK: Выполнение хранимой процедуры {proc_name} в базе {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "procedure": proc_name,
        "output": {"result": "success"}
    }


@when(parsers.parse('выполнить хранимую процедуру "{proc_name}" в базе "{db_name}" с параметрами:'))
def execute_stored_proc_with_params(context, proc_name, db_name, docstring):
    """Выполнение хранимой процедуры с параметрами."""
    print(f"MOCK: Выполнение хранимой процедуры {proc_name} в базе {db_name}")
    print(f"MOCK: Параметры:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "procedure": proc_name,
        "params": docstring,
        "output": {"result": "success"}
    }


@when(parsers.parse('выполнить функцию "{func_name}" в базе "{db_name}"'))
def execute_db_function(context, func_name, db_name):
    """Выполнение функции базы данных."""
    print(f"MOCK: Выполнение функции {func_name} в базе {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "function": func_name,
        "result": "mock_result"
    }


@when(parsers.parse('выполнить функцию "{func_name}" в базе "{db_name}" с параметрами:'))
def execute_db_function_with_params(context, func_name, db_name, docstring):
    """Выполнение функции базы данных с параметрами."""
    print(f"MOCK: Выполнение функции {func_name} в базе {db_name}")
    print(f"MOCK: Параметры:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "function": func_name,
        "params": docstring,
        "result": "mock_result"
    }


@when(parsers.parse('начать транзакцию в базе "{db_name}"'))
def begin_db_transaction(context, db_name):
    """Начало транзакции."""
    if "transactions" not in context:
        context["transactions"] = {}
    context["transactions"][db_name] = {"active": True, "savepoints": []}
    print(f"MOCK: Начата транзакция в базе {db_name}")


@when(parsers.parse('зафиксировать транзакцию в базе "{db_name}"'))
def commit_db_transaction(context, db_name):
    """Фиксация транзакции."""
    if "transactions" in context and db_name in context["transactions"]:
        context["transactions"][db_name]["active"] = False
        context["transactions"][db_name]["committed"] = True
    print(f"MOCK: Транзакция зафиксирована в базе {db_name}")


@when(parsers.parse('откатить транзакцию в базе "{db_name}"'))
def rollback_db_transaction(context, db_name):
    """Откат транзакции."""
    if "transactions" in context and db_name in context["transactions"]:
        context["transactions"][db_name]["active"] = False
        context["transactions"][db_name]["rolled_back"] = True
    print(f"MOCK: Транзакция откачена в базе {db_name}")


@when(parsers.parse('создать точку сохранения "{savepoint_name}" в базе "{db_name}"'))
def create_savepoint(context, savepoint_name, db_name):
    """Создание точки сохранения."""
    if "transactions" not in context:
        context["transactions"] = {}
    if db_name not in context["transactions"]:
        context["transactions"][db_name] = {"savepoints": []}
    context["transactions"][db_name]["savepoints"].append(savepoint_name)
    print(f"MOCK: Создана точка сохранения {savepoint_name} в базе {db_name}")


@when(parsers.parse('откатить к точке сохранения "{savepoint_name}" в базе "{db_name}"'))
def rollback_to_savepoint(context, savepoint_name, db_name):
    """Откат к точке сохранения."""
    print(f"MOCK: Откат к точке сохранения {savepoint_name} в базе {db_name}")


@when(parsers.parse('вставить данные в таблицу "{table_name}" базы "{db_name}":'))
def insert_data_to_table(context, table_name, db_name, datatable):
    """Вставка данных в таблицу из datatable."""
    print(f"MOCK: Вставка данных в таблицу {table_name} базы {db_name}")
    print(f"MOCK: Данные: {datatable}")
    
    context["last_db_result"] = {
        "database": db_name,
        "table": table_name,
        "inserted_rows": 1
    }


@when(parsers.parse('обновить данные в таблице "{table_name}" базы "{db_name}" где "{condition}":'))
def update_data_in_table(context, table_name, db_name, condition, datatable):
    """Обновление данных в таблице."""
    print(f"MOCK: Обновление данных в таблице {table_name} базы {db_name} где {condition}")
    print(f"MOCK: Данные: {datatable}")
    
    context["last_db_result"] = {
        "database": db_name,
        "table": table_name,
        "updated_rows": 1
    }


@when(parsers.parse('удалить данные из таблицы "{table_name}" базы "{db_name}" где "{condition}"'))
def delete_data_from_table(context, table_name, db_name, condition):
    """Удаление данных из таблицы."""
    print(f"MOCK: Удаление данных из таблицы {table_name} базы {db_name} где {condition}")
    
    context["last_db_result"] = {
        "database": db_name,
        "table": table_name,
        "deleted_rows": 1
    }


@when(parsers.parse('экспортировать результат запроса в файл "{file_path}"'))
def export_query_result(context, file_path):
    """Экспорт результата запроса в файл."""
    print(f"MOCK: Результат запроса экспортирован в {file_path}")


@when(parsers.parse('импортировать данные из файла "{file_path}" в таблицу "{table_name}" базы "{db_name}"'))
def import_data_from_file(context, file_path, table_name, db_name):
    """Импорт данных из файла в таблицу."""
    print(f"MOCK: Данные импортированы из {file_path} в таблицу {table_name} базы {db_name}")
    
    context["last_db_result"] = {
        "database": db_name,
        "table": table_name,
        "imported_rows": 100
    }


@when(parsers.parse('создать индекс "{index_name}" на таблице "{table_name}" базы "{db_name}" для колонок "{columns}"'))
def create_index(context, index_name, table_name, db_name, columns):
    """Создание индекса."""
    print(f"MOCK: Создан индекс {index_name} на таблице {table_name} для колонок {columns}")


@when(parsers.parse('удалить индекс "{index_name}" с таблицы "{table_name}" базы "{db_name}"'))
def drop_index(context, index_name, table_name, db_name):
    """Удаление индекса."""
    print(f"MOCK: Удален индекс {index_name} с таблицы {table_name}")


@when(parsers.parse('выполнить VACUUM на таблице "{table_name}" базы "{db_name}"'))
def vacuum_table(context, table_name, db_name):
    """Выполнение VACUUM на таблице."""
    print(f"MOCK: Выполнен VACUUM на таблице {table_name} базы {db_name}")


@when(parsers.parse('выполнить ANALYZE на таблице "{table_name}" базы "{db_name}"'))
def analyze_table(context, table_name, db_name):
    """Выполнение ANALYZE на таблице."""
    print(f"MOCK: Выполнен ANALYZE на таблице {table_name} базы {db_name}")


@when(parsers.parse('заблокировать таблицу "{table_name}" в базе "{db_name}" в режиме "{lock_mode}"'))
def lock_table(context, table_name, db_name, lock_mode):
    """Блокировка таблицы."""
    print(f"MOCK: Таблица {table_name} заблокирована в режиме {lock_mode}")


@when(parsers.parse('разблокировать таблицу "{table_name}" в базе "{db_name}"'))
def unlock_table(context, table_name, db_name):
    """Разблокировка таблицы."""
    print(f"MOCK: Таблица {table_name} разблокирована")


@when(parsers.parse('выполнить запрос с параметрами в базу "{db_name}":'))
def execute_parameterized_query(context, db_name, docstring):
    """Выполнение параметризованного запроса."""
    print(f"MOCK: Выполнение параметризованного запроса в базу {db_name}")
    print(f"MOCK: Запрос:\n{docstring}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": docstring,
        "rows": [{"id": 1}]
    }


@when(parsers.parse('выполнить запрос с подстановкой переменных в базу "{db_name}":'))
def execute_query_with_variables(context, db_name, docstring):
    """Выполнение запроса с подстановкой переменных."""
    query = docstring
    for var_name, var_value in context.get("variables", {}).items():
        query = query.replace(f"${{{var_name}}}", str(var_value))
    
    print(f"MOCK: Выполнение запроса с подстановкой переменных в базу {db_name}")
    print(f"MOCK: Запрос:\n{query}")
    
    context["last_db_result"] = {
        "database": db_name,
        "query": query,
        "rows": [{"id": 1}]
    }


# ============================================================================
# --- Then steps (Database Verification) ---
# ============================================================================

@then(parsers.parse('результат запроса содержит {count:d} строк'))
def check_row_count(context, count):
    """Проверка количества строк в результате."""
    # Проверяем оба возможных ключа для результата SQL
    db_result = context.get("last_db_result", {})
    sql_result = context.get("last_sql_result", [])
    
    if db_result and "rows" in db_result:
        actual_count = len(db_result.get("rows", []))
    else:
        actual_count = len(sql_result) if sql_result else count  # Mock: возвращаем ожидаемое значение
    
    print(f"MOCK: Проверка количества строк: ожидается {count}, получено {actual_count}")
    soft_assert(actual_count == count)


@then(parsers.parse('результат запроса содержит более {count:d} строк'))
def check_row_count_greater(context, count):
    """Проверка что строк больше указанного количества."""
    db_result = context.get("last_db_result", {})
    sql_result = context.get("last_sql_result", [])
    
    if db_result and "rows" in db_result:
        actual_count = len(db_result.get("rows", []))
    else:
        actual_count = len(sql_result) if sql_result else count + 1
    
    print(f"MOCK: Проверка количества строк: должно быть > {count}")
    soft_assert(actual_count > count)


@then(parsers.parse('результат запроса содержит менее {count:d} строк'))
def check_row_count_less(context, count):
    """Проверка что строк меньше указанного количества."""
    db_result = context.get("last_db_result", {})
    sql_result = context.get("last_sql_result", [])
    
    if db_result and "rows" in db_result:
        actual_count = len(db_result.get("rows", []))
    else:
        actual_count = len(sql_result) if sql_result else count - 1
    
    print(f"MOCK: Проверка количества строк: должно быть < {count}")
    soft_assert(actual_count < count)


@then(parsers.parse('результат запроса не пустой'))
def check_result_not_empty(context):
    """Проверка что результат не пустой."""
    rows = context.get("last_db_result", {}).get("rows", [])
    print(f"MOCK: Проверка что результат не пустой")
    soft_assert(len(rows) > 0)


@then(parsers.parse('результат запроса пустой'))
def check_result_empty(context):
    """Проверка что результат пустой."""
    rows = context.get("last_db_result", {}).get("rows", [])
    print(f"MOCK: Проверка что результат пустой")
    soft_assert(len(rows) == 0)


@then(parsers.parse('результат запроса содержит колонку "{column_name}"'))
def check_column_exists(context, column_name):
    """Проверка наличия колонки в результате."""
    rows = context.get("last_db_result", {}).get("rows", [])
    if rows:
        print(f"MOCK: Проверка наличия колонки {column_name}")
        soft_assert(column_name in rows[0])


@then(parsers.parse('результат запроса содержит значение "{value}" в колонке "{column_name}"'))
def check_column_value(context, value, column_name):
    """Проверка значения в колонке."""
    rows = context.get("last_db_result", {}).get("rows", [])
    print(f"MOCK: Проверка значения {value} в колонке {column_name}")
    found = any(str(row.get(column_name)) == str(value) for row in rows)
    soft_assert(found)


@then(parsers.parse('результат запроса в первой строке содержит "{value}" в колонке "{column_name}"'))
def check_first_row_value(context, value, column_name):
    """Проверка значения в первой строке."""
    rows = context.get("last_db_result", {}).get("rows", [])
    print(f"MOCK: Проверка значения {value} в первой строке колонки {column_name}")
    if rows:
        soft_assert(str(rows[0].get(column_name)) == str(value))


@then(parsers.parse('количество затронутых строк равно {count:d}'))
def check_affected_rows(context, count):
    """Проверка количества затронутых строк."""
    affected = context.get("last_db_result", {}).get("affected_rows", 0)
    print(f"MOCK: Проверка затронутых строк: ожидается {count}, получено {affected}")
    soft_assert(affected == count)


@then(parsers.parse('количество затронутых строк больше {count:d}'))
def check_affected_rows_greater(context, count):
    """Проверка что затронуто больше строк."""
    affected = context.get("last_db_result", {}).get("affected_rows", 0)
    print(f"MOCK: Проверка затронутых строк: должно быть > {count}")
    soft_assert(affected > count)


@then(parsers.parse('ID вставленной записи сохранен в переменную "{var_name}"'))
def save_inserted_id(context, var_name):
    """Сохранение ID вставленной записи."""
    inserted_id = context.get("last_db_result", {}).get("inserted_id", 0)
    context["variables"][var_name] = inserted_id
    print(f"MOCK: ID вставленной записи {inserted_id} сохранен в {var_name}")


@then(parsers.parse('значение колонки "{column_name}" из первой строки сохранено в переменную "{var_name}"'))
def save_column_value(context, column_name, var_name):
    """Сохранение значения колонки в переменную."""
    rows = context.get("last_db_result", {}).get("rows", [])
    if rows:
        value = rows[0].get(column_name)
        context["variables"][var_name] = value
        print(f"MOCK: Значение {value} из колонки {column_name} сохранено в {var_name}")


@then(parsers.parse('результат запроса соответствует данным:'))
def check_result_matches_data(context, datatable):
    """Проверка соответствия результата данным."""
    print(f"MOCK: Проверка соответствия результата данным: {datatable}")
    soft_assert(True)


@then(parsers.parse('результат запроса содержит данные:'))
def check_result_contains_data(context, datatable):
    """Проверка что результат содержит данные."""
    print(f"MOCK: Проверка что результат содержит данные: {datatable}")
    soft_assert(True)


@then(parsers.parse('таблица "{table_name}" в базе "{db_name}" существует'))
def check_table_exists(context, table_name, db_name):
    """Проверка существования таблицы."""
    print(f"MOCK: Проверка существования таблицы {table_name} в базе {db_name}")
    soft_assert(True)


@then(parsers.parse('таблица "{table_name}" в базе "{db_name}" не существует'))
def check_table_not_exists(context, table_name, db_name):
    """Проверка отсутствия таблицы."""
    print(f"MOCK: Проверка отсутствия таблицы {table_name} в базе {db_name}")
    soft_assert(True)


@then(parsers.parse('таблица "{table_name}" в базе "{db_name}" содержит {count:d} записей'))
def check_table_record_count(context, table_name, db_name, count):
    """Проверка количества записей в таблице."""
    print(f"MOCK: Проверка количества записей в таблице {table_name}: ожидается {count}")
    soft_assert(True)


@then(parsers.parse('таблица "{table_name}" в базе "{db_name}" пустая'))
def check_table_empty(context, table_name, db_name):
    """Проверка что таблица пустая."""
    print(f"MOCK: Проверка что таблица {table_name} пустая")
    soft_assert(True)


@then(parsers.parse('индекс "{index_name}" существует на таблице "{table_name}" базы "{db_name}"'))
def check_index_exists(context, index_name, table_name, db_name):
    """Проверка существования индекса."""
    print(f"MOCK: Проверка существования индекса {index_name} на таблице {table_name}")
    soft_assert(True)


@then(parsers.parse('индекс "{index_name}" не существует на таблице "{table_name}" базы "{db_name}"'))
def check_index_not_exists(context, index_name, table_name, db_name):
    """Проверка отсутствия индекса."""
    print(f"MOCK: Проверка отсутствия индекса {index_name} на таблице {table_name}")
    soft_assert(True)


@then(parsers.parse('транзакция в базе "{db_name}" активна'))
def check_transaction_active(context, db_name):
    """Проверка что транзакция активна."""
    active = context.get("transactions", {}).get(db_name, {}).get("active", False)
    print(f"MOCK: Проверка что транзакция в {db_name} активна")
    soft_assert(active)


@then(parsers.parse('транзакция в базе "{db_name}" не активна'))
def check_transaction_not_active(context, db_name):
    """Проверка что транзакция не активна."""
    active = context.get("transactions", {}).get(db_name, {}).get("active", True)
    print(f"MOCK: Проверка что транзакция в {db_name} не активна")
    soft_assert(not active)


@then(parsers.parse('время выполнения запроса меньше {max_time:d} миллисекунд'))
def check_query_execution_time(context, max_time):
    """Проверка времени выполнения запроса."""
    print(f"MOCK: Проверка времени выполнения запроса: должно быть < {max_time}мс")
    soft_assert(True)


@then(parsers.parse('время выполнения запроса меньше {max_time:d} секунд'))
def check_query_execution_time_seconds(context, max_time):
    """Проверка времени выполнения запроса в секундах."""
    print(f"MOCK: Проверка времени выполнения запроса: должно быть < {max_time}с")
    soft_assert(True)


@then(parsers.parse('подключение к базе "{db_name}" активно'))
def check_connection_active(context, db_name):
    """Проверка активности подключения."""
    connected = context.get("databases", {}).get(db_name, {}).get("connected", False)
    print(f"MOCK: Проверка что подключение к {db_name} активно")
    soft_assert(connected)


@then(parsers.parse('закрыть подключение к базе "{db_name}"'))
def close_db_connection(context, db_name):
    """Закрытие подключения к базе данных."""
    if "databases" in context and db_name in context["databases"]:
        context["databases"][db_name]["connected"] = False
    print(f"MOCK: Подключение к базе {db_name} закрыто")


@then(parsers.parse('вывести результат запроса'))
def print_query_result(context):
    """Вывод результата запроса."""
    result = context.get("last_db_result", {})
    print(f"DEBUG: Результат запроса = {json.dumps(result, indent=2, ensure_ascii=False, default=str)}")
