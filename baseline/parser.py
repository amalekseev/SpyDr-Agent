"""
Парсер Gherkin шагов из Python файлов pytest-bdd.

Извлекает шаги, определённые с помощью декораторов @given, @when, @then
и сохраняет их в JSON структуру.
"""
import os
import re
import json
import argparse
from pathlib import Path
from typing import Optional


def parse_step_pattern(decorator_line: str, next_lines: list[str]) -> Optional[dict]:
    """
    Парсит декоратор шага и извлекает информацию о нём.
    
    Args:
        decorator_line: Строка с декоратором (@given, @when, @then)
        next_lines: Следующие строки для извлечения имени функции и docstring
    
    Returns:
        Словарь с информацией о шаге или None, если не удалось распарсить
    """
    # Паттерн для декораторов: @given(...), @when(...), @then(...)
    step_type_match = re.match(r'@(given|when|then)\s*\(', decorator_line, re.IGNORECASE)
    if not step_type_match:
        return None
    
    step_type = step_type_match.group(1).lower()
    
    # Извлекаем паттерн шага
    # Варианты: parsers.parse('...'), parsers.parse("..."), просто строка '...' или "..."
    pattern = None
    
    # Ищем parsers.parse('...')
    parse_match = re.search(r'parsers\.parse\s*\(\s*[\'"](.+?)[\'"]\s*\)', decorator_line)
    if parse_match:
        pattern = parse_match.group(1)
    else:
        # Ищем просто строку в декораторе @given('...')
        simple_match = re.search(r'@(?:given|when|then)\s*\(\s*[\'"](.+?)[\'"]\s*\)', decorator_line, re.IGNORECASE)
        if simple_match:
            pattern = simple_match.group(1)
    
    if not pattern:
        return None
    
    # Ищем имя функции в следующих строках
    function_name = None
    docstring = None
    
    for i, line in enumerate(next_lines):
        func_match = re.match(r'def\s+(\w+)\s*\(', line)
        if func_match:
            function_name = func_match.group(1)
            # Ищем docstring после определения функции
            for j in range(i + 1, min(i + 5, len(next_lines))):
                doc_line = next_lines[j].strip()
                if doc_line.startswith('"""') or doc_line.startswith("'''"):
                    # Однострочный docstring
                    doc_match = re.match(r'[\'\"]{3}(.+?)[\'\"]{3}', doc_line)
                    if doc_match:
                        docstring = doc_match.group(1)
                    else:
                        # Многострочный docstring - берём первую строку
                        docstring = doc_line.strip('"\' ')
                    break
            break
    
    return {
        "type": step_type,
        "pattern": pattern,
        "function_name": function_name,
        "docstring": docstring
    }


def parse_steps_file(file_path: str) -> list[dict]:
    """
    Парсит Python файл и извлекает все Gherkin шаги.
    
    Args:
        file_path: Путь к Python файлу
    
    Returns:
        Список словарей с информацией о шагах
    """
    steps = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError) as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
        return steps
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Проверяем, является ли строка декоратором шага
        if re.match(r'@(given|when|then)\s*\(', stripped, re.IGNORECASE):
            # Передаём следующие строки для парсинга
            next_lines = [l.strip() for l in lines[i+1:i+10]]
            step_info = parse_step_pattern(stripped, next_lines)
            
            if step_info:
                step_info["source_file"] = os.path.basename(file_path)
                step_info["line_number"] = i + 1
                steps.append(step_info)
    
    return steps


def parse_steps_directory(directory_path: str) -> dict:
    """
    Парсит все Python файлы в директории и извлекает Gherkin шаги.
    
    Args:
        directory_path: Путь к директории со step-файлами
    
    Returns:
        Словарь с результатами парсинга
    """
    result = {
        "total_steps": 0,
        "steps_by_type": {
            "given": 0,
            "when": 0,
            "then": 0
        },
        "files_parsed": [],
        "steps": []
    }
    
    directory = Path(directory_path)
    
    if not directory.exists():
        raise FileNotFoundError(f"Директория не найдена: {directory_path}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {directory_path}")
    
    # Ищем все Python файлы
    python_files = list(directory.glob("*.py"))
    
    for py_file in python_files:
        file_steps = parse_steps_file(str(py_file))
        
        if file_steps:
            result["files_parsed"].append({
                "file": py_file.name,
                "steps_count": len(file_steps)
            })
            
            for step in file_steps:
                result["steps"].append(step)
                result["steps_by_type"][step["type"]] += 1
            
            result["total_steps"] += len(file_steps)
    
    return result


def save_to_json(data: dict, output_path: str) -> None:
    """
    Сохраняет данные в JSON файл.
    
    Args:
        data: Данные для сохранения
        output_path: Путь к выходному файлу
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Результаты сохранены в: {output_path}")


def main():
    """Точка входа для CLI."""
    parser = argparse.ArgumentParser(
        description="Парсер Gherkin шагов из pytest-bdd файлов"
    )
    parser.add_argument(
        "steps_path",
        help="Путь к директории со step-файлами"
    )
    parser.add_argument(
        "-o", "--output",
        default="steps.json",
        help="Путь к выходному JSON файлу (по умолчанию: steps.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )
    
    args = parser.parse_args()
    
    try:
        result = parse_steps_directory(args.steps_path)
        
        # Сохраняем в JSON
        save_to_json(result, args.output)
        
        # Выводим статистику
        print(f"\nВсего найдено шагов: {result['total_steps']}")
        print(f"  - Given: {result['steps_by_type']['given']}")
        print(f"  - When: {result['steps_by_type']['when']}")
        print(f"  - Then: {result['steps_by_type']['then']}")
        print(f"\nОбработано файлов: {len(result['files_parsed'])}")
        
        if args.verbose:
            print("\nДетали по файлам:")
            for file_info in result["files_parsed"]:
                print(f"  - {file_info['file']}: {file_info['steps_count']} шагов")
        
        return result["total_steps"]
        
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Ошибка: {e}")
        return -1


if __name__ == "__main__":
    exit(main())
