"""CLI entrypoint for pytest-bdd step parser."""

import argparse
import sys

try:
    from core.io_utils import save_json
    from core.step_parser import parse_steps_directory
except ImportError:
    # Allows running as module from project root.
    from baseline.core.io_utils import save_json
    from baseline.core.step_parser import parse_steps_directory


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI parser for step extraction."""
    parser = argparse.ArgumentParser(description="Парсер Gherkin шагов из pytest-bdd файлов")
    parser.add_argument("steps_path", help="Путь к директории со step-файлами")
    parser.add_argument(
        "-o",
        "--output",
        default="steps.json",
        help="Путь к выходному JSON файлу (по умолчанию: steps.json)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")
    return parser


def main() -> int:
    """Run parser CLI and return shell status code."""
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        result = parse_steps_directory(args.steps_path)
        save_json(result, args.output)
        print(f"Результаты сохранены в: {args.output}")
        print(f"\nВсего найдено шагов: {result['total_steps']}")
        print(f"  - Given: {result['steps_by_type']['given']}")
        print(f"  - When: {result['steps_by_type']['when']}")
        print(f"  - Then: {result['steps_by_type']['then']}")
        print(f"  - Step: {result['steps_by_type']['step']}")
        print(f"\nОбработано файлов: {len(result['files_parsed'])}")

        if args.verbose:
            print("\nДетали по файлам:")
            for file_info in result["files_parsed"]:
                print(f"  - {file_info['file']}: {file_info['steps_count']} шагов")

        return result["total_steps"]
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Ошибка: {exc}")
        return -1


if __name__ == "__main__":
    sys.exit(main())
