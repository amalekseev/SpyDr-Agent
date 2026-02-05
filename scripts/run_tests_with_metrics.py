import pytest
import sys
import os

class MetricsCollector:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.total += 1
            if report.outcome == 'passed':
                self.passed += 1
            elif report.outcome == 'failed':
                self.failed += 1
            elif report.outcome == 'skipped':
                self.skipped += 1

def main():
    # Путь к тестам
    test_path = "gherkin/tests"
    
    if not os.path.exists(test_path):
        print(f"Ошибка: Директория {test_path} не найдена.")
        sys.exit(1)

    collector = MetricsCollector()
    
    print(f"--- Запуск тестов в {test_path} ---")
    
    # Запускаем pytest программно
    # -q: quiet mode
    # --no-header: убираем заголовок pytest
    pytest.main([test_path, "-q", "--no-header"], plugins=[collector])

    # Вывод метрик
    print("\n" + "="*30)
    print("ИТОГОВЫЕ МЕТРИКИ")
    print("="*30)
    print(f"Всего тестов:  {collector.total}")
    print(f"Пройдено:      {collector.passed}")
    print(f"Провалено:     {collector.failed}")
    print(f"Пропущено:     {collector.skipped}")
    
    if collector.total > 0:
        pass_rate = (collector.passed / (collector.total - collector.skipped)) * 100 if (collector.total - collector.skipped) > 0 else 0
        print(f"Pass Rate:     {pass_rate:.2f}%")
    else:
        print("Тесты не были найдены или запущены.")
    print("="*30)

if __name__ == "__main__":
    main()
