"""CLI entrypoint for the baseline LLM conversion pipeline."""

import argparse
import sys

try:
    from core.constants import (
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_LLM_PROVIDER,
        DEFAULT_MODEL,
        DEFAULT_PHOENIX_ENDPOINT,
        DEFAULT_PHOENIX_SERVICE_NAME,
        DEFAULT_RAG_TOP_K,
    )
    from core.io_utils import save_json
    from core.pipeline import run_pipeline
except ImportError:
    # Allows running as module from project root.
    from baseline.core.constants import (
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_LLM_PROVIDER,
        DEFAULT_MODEL,
        DEFAULT_PHOENIX_ENDPOINT,
        DEFAULT_PHOENIX_SERVICE_NAME,
        DEFAULT_RAG_TOP_K,
    )
    from baseline.core.io_utils import save_json
    from baseline.core.pipeline import run_pipeline


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI parser for baseline converter."""
    parser = argparse.ArgumentParser(
        description="Baseline LLM Pipeline для конвертации ручных тестов в Gherkin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python baseline/main.py manual_tests/tests/
  python baseline/main.py manual_tests/tests/ -o output/features/
  python baseline/main.py manual_tests/tests/ --steps custom_steps.json
  python baseline/main.py manual_tests/tests/ --model gpt-4o-mini -v
        """,
    )
    parser.add_argument("input_dir", help="Путь к директории с ручными тестами (.txt файлы)")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Путь к директории для сохранения feature файлов (по умолчанию: baseline/features/)",
    )
    parser.add_argument(
        "-s",
        "--steps",
        default=None,
        help="Путь к файлу steps.json с доступными шагами (по умолчанию: baseline/steps.json)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM-модель для использования (по умолчанию: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "gigachat"],
        default=DEFAULT_LLM_PROVIDER,
        help=f"Провайдер LLM/эмбеддингов (по умолчанию: {DEFAULT_LLM_PROVIDER})",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="URL подключения к PostgreSQL с pgvector (или BASELINE_RAG_DB_URL в окружении)",
    )
    parser.add_argument(
        "--rag-top-k",
        type=int,
        default=DEFAULT_RAG_TOP_K,
        help=f"Количество кандидатов, запрашиваемых из RAG на один поиск (по умолчанию: {DEFAULT_RAG_TOP_K})",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=(
            "Модель эмбеддингов для индексации и поиска шагов "
            f"(по умолчанию: {DEFAULT_EMBEDDING_MODEL})"
        ),
    )
    parser.add_argument(
        "--trace-phoenix",
        action="store_true",
        help="Включить OpenTelemetry трейсинг в Phoenix",
    )
    parser.add_argument(
        "--phoenix-endpoint",
        default=DEFAULT_PHOENIX_ENDPOINT,
        help=f"OTLP endpoint Phoenix (по умолчанию: {DEFAULT_PHOENIX_ENDPOINT})",
    )
    parser.add_argument(
        "--phoenix-service-name",
        default=DEFAULT_PHOENIX_SERVICE_NAME,
        help=f"service.name в трейсе (по умолчанию: {DEFAULT_PHOENIX_SERVICE_NAME})",
    )
    parser.add_argument(
        "--reindex-steps",
        action="store_true",
        help="Переиндексировать шаги из steps.json в PostgreSQL перед запуском конвертации",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")
    parser.add_argument(
        "--save-results",
        type=str,
        default=None,
        help="Путь для сохранения результатов в JSON формате",
    )
    return parser


def main() -> int:
    """Run CLI and return shell status code."""
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        results = run_pipeline(
            input_dir=args.input_dir,
            output_dir=args.output,
            steps_file=args.steps,
            model=args.model,
            llm_provider=args.llm_provider,
            db_url=args.db_url,
            rag_top_k=args.rag_top_k,
            embedding_model=args.embedding_model,
            trace_phoenix=args.trace_phoenix,
            phoenix_endpoint=args.phoenix_endpoint,
            phoenix_service_name=args.phoenix_service_name,
            reindex_steps=args.reindex_steps,
            verbose=args.verbose,
        )
        if args.save_results:
            save_json(results, args.save_results)
            print(f"\nРезультаты сохранены в: {args.save_results}")
        return 1 if results["failed"] > 0 else 0
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Ошибка: {exc}")
        return 1
    except ValueError as exc:
        print(f"Ошибка конфигурации: {exc}")
        return 1
    except Exception as exc:
        print(f"Неожиданная ошибка: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
