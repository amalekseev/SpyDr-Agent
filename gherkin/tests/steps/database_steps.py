"""
Database шаги для тестирования.
Включает шаги для выполнения SQL запросов.
Примечание: шаги проверки результатов уже есть в common_steps.py
"""
from pytest_bdd import when, parsers


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
