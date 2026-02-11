"""Pipeline orchestration for manual tests to Gherkin conversion."""

from pathlib import Path
from typing import Any, Optional

from .constants import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PHOENIX_ENDPOINT,
    DEFAULT_PHOENIX_SERVICE_NAME,
    DEFAULT_RAG_TOP_K,
    DEFAULT_STEPS_FILE,
)
from .io_utils import list_text_files, read_text_with_fallback, write_text_with_trailing_newline
from .llm_converter import build_feature_plan, feature_plan_to_json_text, get_openai_client
from .models import FileProcessResult, PipelineResult
from .rag_store import StepRAGStore, resolve_database_url
from .step_renderer import render_feature_from_plan
from .steps_catalog import build_steps_index, load_steps
from .tracing import get_tracer, setup_phoenix_tracing

MAX_RENDER_REPAIR_ATTEMPTS = 3
TRACER = get_tracer(__name__)


def generate_feature_name(file_path: Path) -> str:
    """Generate a human-friendly feature title from source file name."""
    words = file_path.stem.replace("_", " ").replace("-", " ")
    return words.title()


def process_test_file(
    *,
    client,
    test_file: Path,
    output_dir: Path,
    rag_store: StepRAGStore,
    steps_index: dict[str, dict[str, Any]],
    model: str,
    rag_top_k: int,
    verbose: bool = False,
) -> tuple[FileProcessResult, dict[str, int]]:
    """Convert a single txt file into a feature file."""
    result = FileProcessResult(source_file=str(test_file))
    rag_metrics = {"rag_tool_calls": 0, "rag_unresolved_steps": 0, "rag_validation_errors": 0}
    with TRACER.start_as_current_span("baseline.process_test_file") as span:
        span.set_attribute("baseline.file_name", test_file.name)
        span.set_attribute("baseline.model", model)
        span.set_attribute("baseline.rag_top_k", rag_top_k)
        try:
            if verbose:
                print("  [pipeline] Чтение входного теста...")
            test_content = read_text_with_fallback(test_file)
            if not test_content.strip():
                result.status = "skipped"
                result.error = "Файл пустой"
                span.set_attribute("baseline.file_status", "skipped")
                return result, rag_metrics

            feature_name = generate_feature_name(test_file)
            if verbose:
                print(f"  Конвертация: {test_file.name} -> {feature_name}")
                print("  [pipeline] Запуск agent/tool-calling...")

            repair_feedback: str | None = None
            gherkin_content = ""
            render_metrics = {"rag_unresolved_steps": 0, "rag_validation_errors": 0}
            for attempt in range(1, MAX_RENDER_REPAIR_ATTEMPTS + 1):
                if verbose and attempt > 1:
                    print(
                        f"  [pipeline] Повторная попытка сборки плана: {attempt}/{MAX_RENDER_REPAIR_ATTEMPTS}"
                    )
                feature_plan, tool_calls = build_feature_plan(
                    client=client,
                    test_content=test_content,
                    feature_name=feature_name,
                    model=model,
                    rag_store=rag_store,
                    rag_top_k=rag_top_k,
                    verbose=verbose,
                    repair_feedback=repair_feedback,
                )
                rag_metrics["rag_tool_calls"] += tool_calls
                if verbose:
                    print("  [pipeline] Рендер feature из step_id...")
                try:
                    gherkin_content, render_metrics = render_feature_from_plan(
                        feature_plan=feature_plan, steps_index=steps_index
                    )
                    break
                except ValueError as render_exc:
                    rag_metrics["rag_validation_errors"] += 1
                    if attempt >= MAX_RENDER_REPAIR_ATTEMPTS:
                        span.record_exception(render_exc)
                        raise
                    repair_feedback = (
                        f"Ошибка валидации/рендера: {render_exc}\n"
                        "Текущий план:\n"
                        f"{feature_plan_to_json_text(feature_plan)}"
                    )
                    if verbose:
                        print(f"  [pipeline] План не прошел валидацию: {render_exc}")
                        print("  [pipeline] Запрашиваю исправленный JSON-план у модели...")

            rag_metrics["rag_unresolved_steps"] = render_metrics["rag_unresolved_steps"]
            rag_metrics["rag_validation_errors"] += render_metrics["rag_validation_errors"]

            output_file = output_dir / f"{test_file.stem}.feature"
            if verbose:
                print(f"  [pipeline] Запись результата в {output_file}")
            write_text_with_trailing_newline(gherkin_content, output_file)

            result.status = "success"
            result.output_file = str(output_file)
            span.set_attribute("baseline.file_status", "success")
            return result, rag_metrics
        except Exception as exc:
            result.status = "error"
            result.error = str(exc)
            span.set_attribute("baseline.file_status", "error")
            span.record_exception(exc)
            return result, rag_metrics


def run_pipeline(
    input_dir: str,
    output_dir: Optional[str] = None,
    steps_file: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    db_url: Optional[str] = None,
    rag_top_k: int = DEFAULT_RAG_TOP_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    trace_phoenix: bool = False,
    phoenix_endpoint: str = DEFAULT_PHOENIX_ENDPOINT,
    phoenix_service_name: str = DEFAULT_PHOENIX_SERVICE_NAME,
    reindex_steps: bool = False,
    verbose: bool = False,
) -> dict:
    """Run the full conversion pipeline and return serializable stats."""
    setup_phoenix_tracing(
        enabled=trace_phoenix,
        endpoint=phoenix_endpoint,
        service_name=phoenix_service_name,
    )
    output_path = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    steps_path = Path(steps_file) if steps_file else DEFAULT_STEPS_FILE

    results = PipelineResult(
        input_directory=input_dir,
        output_directory=str(output_path),
        steps_file=str(steps_path),
        model=model,
    )

    with TRACER.start_as_current_span("baseline.run_pipeline") as span:
        span.set_attribute("baseline.input_dir", input_dir)
        span.set_attribute("baseline.output_dir", str(output_path))
        span.set_attribute("baseline.model", model)
        span.set_attribute("baseline.embedding_model", embedding_model)
        span.set_attribute("baseline.rag_top_k", rag_top_k)
        span.set_attribute("baseline.trace_phoenix", trace_phoenix)

        print("=" * 60)
        print("Baseline LLM Pipeline - Конвертация тестов в Gherkin")
        print("=" * 60)
        print(f"Входная директория: {input_dir}")
        print(f"Выходная директория: {output_path}")
        print(f"Файл шагов: {steps_path}")
        print(f"Модель: {model}")
        print(f"Embedding model: {embedding_model}")
        print(f"RAG top_k: {rag_top_k}")
        print(f"Phoenix tracing: {'on' if trace_phoenix else 'off'}")
        if trace_phoenix:
            print(f"Phoenix endpoint: {phoenix_endpoint}")
            print(f"Phoenix service: {phoenix_service_name}")
        print()

        print("Загрузка доступных шагов...")
        steps_data = load_steps(steps_path)
        steps_index = build_steps_index(steps_data)
        print(f"Загружено шагов: {steps_data['total_steps']}")
        print(f"  - Given: {steps_data['steps_by_type']['given']}")
        print(f"  - When: {steps_data['steps_by_type']['when']}")
        print(f"  - Then: {steps_data['steps_by_type']['then']}")
        print()

        database_url = resolve_database_url(db_url)
        client = get_openai_client()
        rag_store = StepRAGStore(db_url=database_url, client=client, embedding_model=embedding_model)
        print("Инициализация RAG-хранилища...")
        rag_store.ensure_schema()
        if reindex_steps:
            upserted = rag_store.upsert_steps(steps_data["steps"], verbose=verbose)
            print(f"Индекс шагов обновлен: {upserted} записей")
        print()

        test_files = list_text_files(input_dir)
        results.total_files = len(test_files)
        if not test_files:
            print(f"Предупреждение: в директории {input_dir} не найдено .txt файлов")
            print("Нет файлов для обработки.")
            return results.to_dict()

        print(f"Найдено файлов с тестами: {len(test_files)}")
        print()

        for idx, test_file in enumerate(test_files, 1):
            print(f"[{idx}/{len(test_files)}] Обработка: {test_file.name}")
            file_result, rag_metrics = process_test_file(
                client=client,
                test_file=test_file,
                output_dir=output_path,
                rag_store=rag_store,
                steps_index=steps_index,
                model=model,
                rag_top_k=rag_top_k,
                verbose=verbose,
            )
            results.files.append(file_result.to_dict())
            results.rag_tool_calls += rag_metrics["rag_tool_calls"]
            results.rag_unresolved_steps += rag_metrics["rag_unresolved_steps"]
            results.rag_validation_errors += rag_metrics["rag_validation_errors"]

            if file_result.status == "success":
                results.successful += 1
                print(f"  ✓ Сохранено: {file_result.output_file}")
            elif file_result.status == "skipped":
                results.skipped += 1
                print(f"  ⊘ Пропущено: {file_result.error}")
            else:
                results.failed += 1
                print(f"  ✗ Ошибка: {file_result.error}")

        print()
        print("=" * 60)
        print("Итоги:")
        print(f"  Всего файлов: {results.total_files}")
        print(f"  Успешно: {results.successful}")
        print(f"  Пропущено: {results.skipped}")
        print(f"  Ошибок: {results.failed}")
        print(f"  RAG tool-вызовов: {results.rag_tool_calls}")
        print(f"  RAG неразрешенных шагов: {results.rag_unresolved_steps}")
        print(f"  RAG ошибок валидации: {results.rag_validation_errors}")
        print("=" * 60)

        span.set_attribute("baseline.total_files", results.total_files)
        span.set_attribute("baseline.successful", results.successful)
        span.set_attribute("baseline.failed", results.failed)
        span.set_attribute("baseline.skipped", results.skipped)
        return results.to_dict()
