import sys
from pathlib import Path
from pytest_bdd import scenarios

# Добавляем путь к gherkin/tests в sys.path
gherkin_tests_path = Path(__file__).parents[2] / "gherkin" / "tests"
sys.path.insert(0, str(gherkin_tests_path))

# Импортируем шаги напрямую из файлов (без пакета steps)
from steps.common_steps import *
from steps.database_steps import *
from steps.rest_api_steps import *
from steps.ui_steps import *
from steps.kafka_steps import *

# Загружаем feature файлы из текущей директории (baseline/features/)
scenarios('.')