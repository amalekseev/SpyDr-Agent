"""
Baseline LLM Pipeline для конвертации ручных тестов в Gherkin feature файлы.

Использование:
    python baseline/main.py <путь_к_директории_с_тестами>
    python baseline/main.py manual_tests/tests/

Пайплайн:
1. Извлекает все .txt файлы из указанной директории
2. Загружает доступные шаги из steps.json
3. Для каждого файла вызывает LLM для генерации Gherkin feature с учётом доступных шагов
4. Сохраняет результаты в baseline/features/
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Путь к файлу с шагами по умолчанию
DEFAULT_STEPS_FILE = Path(__file__).parent / "steps.json"


# Системный промпт для LLM
SYSTEM_PROMPT = (
    "Ты - эксперт по тестированию ПО, специализирующийся на написании Gherkin сценариев.\n\n"
    "Твоя задача - конвертировать ручные тесты, написанные на естественном языке, "
    "в формат Gherkin (feature файлы).\n\n"
    "ВАЖНО: Ты ДОЛЖЕН использовать ТОЛЬКО шаги из предоставленного списка доступных шагов. "
    "Не придумывай новые шаги - используй только существующие паттерны.\n\n"
    "Правила конвертации:\n"
    "1. Каждый тест должен стать отдельным Scenario\n"
    "2. Используй ключевые слова: Feature, Scenario, Given, When, Then, And\n"
    "3. Используй ТОЛЬКО шаги из списка доступных шагов, подставляя нужные значения в параметры\n"
    '4. Для JSON/XML данных используй многострочные строки с тройными кавычками (""")\n'
    "5. Для табличных данных используй Gherkin таблицы с | разделителями\n"
    "6. Сохраняй все технические детали: URL, имена серверов, названия полей, значения\n"
    "7. Используй русский язык для описания шагов\n"
    "8. Добавляй теги (@tag) для категоризации тестов, если это уместно\n"
    "9. Параметры в шагах обозначены в фигурных скобках, например {url}, {name}, {value}\n\n"
    "Верни ТОЛЬКО содержимое feature файла, без дополнительных пояснений или markdown разметки."
)


def get_openai_client() -> OpenAI:
    """Создаёт и возвращает клиент OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY не найден. Установите переменную окружения или создайте .env файл."
        )
    return OpenAI(api_key=api_key)


def load_steps(steps_file: Path) -> dict:
    """
    Загружает шаги из JSON файла.
    
    Args:
        steps_file: Путь к файлу steps.json
    
    Returns:
        Словарь с данными о шагах
    """
    if not steps_file.exists():
        raise FileNotFoundError(f"Файл шагов не найден: {steps_file}")
    
    with open(steps_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_steps_for_prompt(steps_data: dict) -> str:
    """
    Форматирует шаги для включения в промпт LLM.
    
    Args:
        steps_data: Данные о шагах из steps.json
    
    Returns:
        Отформатированная строка со списком шагов
    """
    lines = []
    lines.append("ДОСТУПНЫЕ ШАГИ:")
    lines.append(f"Всего шагов: {steps_data['total_steps']}")
    lines.append("")
    
    # Группируем шаги по типу
    steps_by_type = {"given": [], "when": [], "then": []}
    
    for step in steps_data.get("steps", []):
        step_type = step.get("type", "").lower()
        if step_type in steps_by_type:
            steps_by_type[step_type].append(step)
    
    # Форматируем Given шаги
    lines.append("=== GIVEN (предусловия) ===")
    for step in steps_by_type["given"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        if docstring:
            lines.append(f"  Given {pattern}  # {docstring}")
        else:
            lines.append(f"  Given {pattern}")
    lines.append("")
    
    # Форматируем When шаги
    lines.append("=== WHEN (действия) ===")
    for step in steps_by_type["when"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        if docstring:
            lines.append(f"  When {pattern}  # {docstring}")
        else:
            lines.append(f"  When {pattern}")
    lines.append("")
    
    # Форматируем Then шаги
    lines.append("=== THEN (проверки) ===")
    for step in steps_by_type["then"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        if docstring:
            lines.append(f"  Then {pattern}  # {docstring}")
        else:
            lines.append(f"  Then {pattern}")
    
    return "\n".join(lines)


def extract_test_files(directory: str) -> list[Path]:
    """
    Извлекает все .txt файлы из указанной директории.
    
    Args:
        directory: Путь к директории с ручными тестами
    
    Returns:
        Список путей к файлам с тестами
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Директория не найдена: {directory}")
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {directory}")
    
    # Ищем все .txt файлы
    test_files = sorted(dir_path.glob("*.txt"))
    
    if not test_files:
        print(f"Предупреждение: в директории {directory} не найдено .txt файлов")
    
    return test_files


def read_test_file(file_path: Path) -> str:
    """
    Читает содержимое файла с тестом.
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        Содержимое файла
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Пробуем другую кодировку
        with open(file_path, 'r', encoding='cp1251') as f:
            return f.read()


def generate_feature_name(file_path: Path) -> str:
    """
    Генерирует имя feature на основе имени файла.
    
    Args:
        file_path: Путь к исходному файлу
    
    Returns:
        Имя для feature (без расширения, с заменой подчёркиваний на пробелы)
    """
    stem = file_path.stem
    # Преобразуем snake_case в Title Case
    words = stem.replace('_', ' ').replace('-', ' ')
    return words.title()


def convert_to_gherkin(
    client: OpenAI,
    test_content: str,
    feature_name: str,
    available_steps: str,
    model: str = "gpt-4o"
) -> str:
    """
    Конвертирует ручной тест в Gherkin формат с помощью LLM.
    
    Args:
        client: Клиент OpenAI
        test_content: Содержимое ручного теста
        feature_name: Название feature
        available_steps: Отформатированный список доступных шагов
        model: Модель OpenAI для использования
    
    Returns:
        Содержимое feature файла в формате Gherkin
    """
    user_prompt = f"""Конвертируй следующий ручной тест в Gherkin feature файл.

Название Feature: {feature_name}

{available_steps}

---

Содержимое теста для конвертации:
---
{test_content}
---

Используй ТОЛЬКО шаги из списка выше. Подставляй конкретные значения вместо параметров в фигурных скобках.
Сгенерируй полный feature файл в формате Gherkin."""
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        #temperature=0.3
    )
    
    return response.choices[0].message.content.strip()


def clean_gherkin_output(content: str) -> str:
    """
    Очищает вывод LLM от возможной markdown разметки.
    
    Args:
        content: Сырой вывод от LLM
    
    Returns:
        Очищенное содержимое feature файла
    """
    # Удаляем markdown code blocks если есть
    if content.startswith("```"):
        lines = content.split('\n')
        # Убираем первую строку с ```gherkin или ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Убираем последнюю строку с ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    return content.strip()


def save_feature_file(content: str, output_path: Path) -> None:
    """
    Сохраняет feature файл.
    
    Args:
        content: Содержимое feature файла
        output_path: Путь для сохранения
    """
    # Создаём директорию если не существует
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
        # Добавляем перевод строки в конце файла
        if not content.endswith('\n'):
            f.write('\n')


def process_test_file(
    client: OpenAI,
    test_file: Path,
    output_dir: Path,
    available_steps: str,
    model: str = "gpt-4o",
    verbose: bool = False
) -> dict:
    """
    Обрабатывает один файл с тестом.
    
    Args:
        client: Клиент OpenAI
        test_file: Путь к файлу с тестом
        output_dir: Директория для сохранения feature файлов
        available_steps: Отформатированный список доступных шагов
        model: Модель OpenAI
        verbose: Подробный вывод
    
    Returns:
        Словарь с результатом обработки
    """
    result = {
        "source_file": str(test_file),
        "status": "pending",
        "output_file": None,
        "error": None
    }
    
    try:
        # Читаем содержимое теста
        test_content = read_test_file(test_file)
        
        if not test_content.strip():
            result["status"] = "skipped"
            result["error"] = "Файл пустой"
            return result
        
        # Генерируем имя feature
        feature_name = generate_feature_name(test_file)
        
        if verbose:
            print(f"  Конвертация: {test_file.name} -> {feature_name}")
        
        # Конвертируем в Gherkin
        gherkin_content = convert_to_gherkin(
            client, test_content, feature_name, available_steps, model
        )
        
        # Очищаем от markdown разметки
        gherkin_content = clean_gherkin_output(gherkin_content)
        
        # Формируем путь для сохранения
        output_file = output_dir / f"{test_file.stem}.feature"
        
        # Сохраняем
        save_feature_file(gherkin_content, output_file)
        
        result["status"] = "success"
        result["output_file"] = str(output_file)
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


def run_pipeline(
    input_dir: str,
    output_dir: Optional[str] = None,
    steps_file: Optional[str] = None,
    model: str = "gpt-4.1",
    verbose: bool = False
) -> dict:
    """
    Запускает пайплайн конвертации ручных тестов в Gherkin.
    
    Args:
        input_dir: Путь к директории с ручными тестами
        output_dir: Путь к директории для сохранения feature файлов
        steps_file: Путь к файлу steps.json с доступными шагами
        model: Модель OpenAI для использования
        verbose: Подробный вывод
    
    Returns:
        Словарь с результатами работы пайплайна
    """
    # Определяем выходную директорию
    if output_dir is None:
        # По умолчанию сохраняем в baseline/features/
        script_dir = Path(__file__).parent
        output_dir = script_dir / "features"
    else:
        output_dir = Path(output_dir)
    
    # Определяем файл с шагами
    if steps_file is None:
        steps_path = DEFAULT_STEPS_FILE
    else:
        steps_path = Path(steps_file)
    
    results = {
        "input_directory": input_dir,
        "output_directory": str(output_dir),
        "steps_file": str(steps_path),
        "model": model,
        "total_files": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "files": []
    }
    
    print("=" * 60)
    print("Baseline LLM Pipeline - Конвертация тестов в Gherkin")
    print("=" * 60)
    print(f"Входная директория: {input_dir}")
    print(f"Выходная директория: {output_dir}")
    print(f"Файл шагов: {steps_path}")
    print(f"Модель: {model}")
    print()
    
    # Загружаем доступные шаги
    print("Загрузка доступных шагов...")
    steps_data = load_steps(steps_path)
    available_steps = format_steps_for_prompt(steps_data)
    print(f"Загружено шагов: {steps_data['total_steps']}")
    print(f"  - Given: {steps_data['steps_by_type']['given']}")
    print(f"  - When: {steps_data['steps_by_type']['when']}")
    print(f"  - Then: {steps_data['steps_by_type']['then']}")
    print()
    
    # Извлекаем файлы с тестами
    test_files = extract_test_files(input_dir)
    results["total_files"] = len(test_files)
    
    if not test_files:
        print("Нет файлов для обработки.")
        return results
    
    print(f"Найдено файлов с тестами: {len(test_files)}")
    print()
    
    # Создаём клиент OpenAI
    client = get_openai_client()
    
    # Обрабатываем каждый файл
    for i, test_file in enumerate(test_files, 1):
        print(f"[{i}/{len(test_files)}] Обработка: {test_file.name}")
        
        file_result = process_test_file(
            client=client,
            test_file=test_file,
            output_dir=output_dir,
            available_steps=available_steps,
            model=model,
            verbose=verbose
        )
        
        results["files"].append(file_result)
        
        if file_result["status"] == "success":
            results["successful"] += 1
            print(f"  ✓ Сохранено: {file_result['output_file']}")
        elif file_result["status"] == "skipped":
            results["skipped"] += 1
            print(f"  ⊘ Пропущено: {file_result['error']}")
        else:
            results["failed"] += 1
            print(f"  ✗ Ошибка: {file_result['error']}")
    
    # Выводим итоги
    print()
    print("=" * 60)
    print("Итоги:")
    print(f"  Всего файлов: {results['total_files']}")
    print(f"  Успешно: {results['successful']}")
    print(f"  Пропущено: {results['skipped']}")
    print(f"  Ошибок: {results['failed']}")
    print("=" * 60)
    
    return results


def main():
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(
        description="Baseline LLM Pipeline для конвертации ручных тестов в Gherkin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python baseline/main.py manual_tests/tests/
  python baseline/main.py manual_tests/tests/ -o output/features/
  python baseline/main.py manual_tests/tests/ --steps custom_steps.json
  python baseline/main.py manual_tests/tests/ --model gpt-4o-mini -v
        """
    )
    
    parser.add_argument(
        "input_dir",
        help="Путь к директории с ручными тестами (.txt файлы)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Путь к директории для сохранения feature файлов (по умолчанию: baseline/features/)"
    )
    
    parser.add_argument(
        "-s", "--steps",
        default=None,
        help="Путь к файлу steps.json с доступными шагами (по умолчанию: baseline/steps.json)"
    )
    
    parser.add_argument(
        "-m", "--model",
        default="gpt-4.1-nano",
        help="Модель OpenAI для использования (по умолчанию: gpt-4o)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )
    
    parser.add_argument(
        "--save-results",
        type=str,
        default=None,
        help="Путь для сохранения результатов в JSON формате"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_pipeline(
            input_dir=args.input_dir,
            output_dir=args.output,
            steps_file=args.steps,
            model=args.model,
            verbose=args.verbose
        )
        
        # Сохраняем результаты если указан путь
        if args.save_results:
            with open(args.save_results, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\nРезультаты сохранены в: {args.save_results}")
        
        # Возвращаем код ошибки если были неудачные конвертации
        if results["failed"] > 0:
            return 1
        return 0
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        return 1
    except NotADirectoryError as e:
        print(f"Ошибка: {e}")
        return 1
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        return 1
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
