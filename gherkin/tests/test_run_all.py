import pytest
from pytest_bdd import scenarios
import os

# Автоматически находим все .feature файлы в папке features
# и связываем их с реализованными шагами
scenarios('../features')

# Импортируем шаги, чтобы pytest-bdd их "видел"
from steps.common_steps import *
