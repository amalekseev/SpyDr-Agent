import pytest
import sys
import os
import json
import re
import shutil
from pathlib import Path
from pytest_bdd.gherkin_parser import Parser
import parse

class MetricsCollector:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.failures: list[tuple[str, str]] = []

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.total += 1
            if report.outcome == 'passed':
                self.passed += 1
            elif report.outcome == 'failed':
                self.failed += 1
                self.failures.append((report.nodeid, report.longreprtext))
            elif report.outcome == 'skipped':
                self.skipped += 1

def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Не удалось прочитать {path}: {exc}")
        return None


SCENARIO_RE = re.compile(
    r"^\s*(Scenario Outline|Scenario|Сценарий|Структура сценария)\s*:",
    re.MULTILINE,
)


def _count_scenarios_in_text(text: str) -> int:
    return len(SCENARIO_RE.findall(text))


def _load_step_patterns(steps_path: Path) -> dict[str, list[parse.Parser]]:
    data = json.loads(steps_path.read_text(encoding="utf-8"))
    patterns: dict[str, list[parse.Parser]] = {"given": [], "when": [], "then": []}
    for step in data.get("steps", []):
        step_type = step.get("type")
        pattern = step.get("pattern")
        if step_type not in patterns or not pattern:
            continue
        try:
            patterns[step_type].append(parse.Parser(pattern))
        except Exception:
            continue
    return patterns


def _step_matches(patterns: dict[str, list[parse.Parser]], keyword: str, text: str) -> bool:
    keyword = keyword.strip()
    if keyword in {"And", "But"}:
        parsers = patterns["given"] + patterns["when"] + patterns["then"]
    else:
        step_type = keyword.lower()
        parsers = patterns.get(step_type, [])
    for parser in parsers:
        if parser.parse(text) is not None:
            return True
    return False


def _scenario_is_runnable(patterns: dict[str, list[parse.Parser]], scenario: dict) -> tuple[bool, str | None]:
    for step in scenario.get("steps", []):
        if not _step_matches(patterns, step.get("keyword", ""), step.get("text", "")):
            keyword = step.get("keyword", "").strip()
            text = step.get("text", "")
            return False, f"missing step: {keyword} {text}"
    return True, None


def _extract_runnable_scenarios(
    content: str,
    patterns: dict[str, list[parse.Parser]],
) -> tuple[str | None, list[tuple[str, str]]]:
    parser = Parser()
    ast = parser.parse(content)
    feature = ast.get("feature", {})
    children = feature.get("children", [])
    lines = content.splitlines()
    skipped_scenarios: list[tuple[str, str]] = []

    scenario_blocks = []
    for child in children:
        scenario = child.get("scenario")
        if not scenario:
            continue
        scenario_line = scenario.get("location", {}).get("line", 1)
        tag_lines = [t.get("location", {}).get("line", scenario_line) for t in scenario.get("tags", [])]
        start_line = min([scenario_line] + tag_lines)
        scenario_blocks.append((start_line, scenario))

    if not scenario_blocks:
        return None, skipped_scenarios

    scenario_blocks.sort(key=lambda item: item[0])
    starts = [start for start, _ in scenario_blocks]
    blocks = []
    for idx, (start_line, scenario) in enumerate(scenario_blocks):
        end_line = (starts[idx + 1] - 1) if idx + 1 < len(starts) else len(lines)
        blocks.append((start_line, end_line, scenario))

    first_start = scenario_blocks[0][0]
    header_lines = lines[: first_start - 1]
    kept_lines = list(header_lines)
    kept_any = False

    for start_line, end_line, scenario in blocks:
        runnable, reason = _scenario_is_runnable(patterns, scenario)
        if not runnable:
            scenario_name = scenario.get("name", "Unnamed scenario")
            skipped_scenarios.append((scenario_name, reason or "missing step"))
            continue
        kept_any = True
        if kept_lines and kept_lines[-1].strip():
            kept_lines.append("")
        kept_lines.extend(lines[start_line - 1 : end_line])

    if not kept_any:
        return None, skipped_scenarios

    return "\n".join(kept_lines) + ("\n" if content.endswith("\n") else ""), skipped_scenarios


def collect_feature_files(
    test_path: str,
    steps_path: Path,
) -> tuple[list[Path], list[tuple[Path, str]], int, dict[Path, str], list[tuple[str, str]]]:
    test_dir = Path(test_path)
    parser = Parser()
    patterns = _load_step_patterns(steps_path)
    valid: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    total_scenarios = 0
    filtered_content: dict[Path, str] = {}
    skipped_scenarios: list[tuple[str, str]] = []

    for feature_file in test_dir.rglob("*.feature"):
        if not feature_file.is_file():
            continue
        content = _safe_read_text(feature_file)
        if content is None:
            reason = "read_error"
        elif not content.strip():
            reason = "empty_file"
        else:
            total_scenarios += _count_scenarios_in_text(content)
            try:
                parser.parse(content)
                runnable_content, scenario_skips = _extract_runnable_scenarios(content, patterns)
                for scenario_name, reason in scenario_skips:
                    skipped_scenarios.append((f"{feature_file.name} :: {scenario_name}", reason))
                if runnable_content is None:
                    skipped.append((feature_file, "no_runnable_scenarios"))
                else:
                    valid.append(feature_file)
                    filtered_content[feature_file] = runnable_content
                continue
            except Exception as exc:
                reason = f"parse_error: {exc}"

        skipped.append((feature_file, reason))

    return valid, skipped, total_scenarios, filtered_content, skipped_scenarios


def main():
    # Путь к тестам
    test_path = "baseline/features"

    if not os.path.exists(test_path):
        print(f"Ошибка: Директория {test_path} не найдена.")
        sys.exit(1)

    steps_path = Path("baseline/steps.json")
    valid_features, skipped, total_scenarios, filtered_content, skipped_scenarios = collect_feature_files(
        test_path,
        steps_path,
    )
    if skipped:
        print("--- Пропущены невалидные feature файлы ---")
        for source, reason in skipped:
            print(f"- {source} ({reason})")
        print("------------------------------------------")
    if skipped_scenarios:
        print("--- Пропущены сценарии без шагов ---")
        for scenario_name, reason in skipped_scenarios:
            print(f"- {scenario_name} ({reason})")
        print("------------------------------------")

    if not valid_features:
        collector = MetricsCollector()
    else:
        run_dir = Path(test_path).parent / "features_tmp_run"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(test_path) / "test_baseline.py", run_dir / "test_baseline.py")

        for feature_file in valid_features:
            run_path = run_dir / feature_file.name
            run_path.write_text(filtered_content[feature_file], encoding="utf-8")

        collector = MetricsCollector()

        print(f"--- Запуск тестов в {run_dir} ---")

        # Запускаем pytest программно
        # -q: quiet mode
        # --no-header: убираем заголовок pytest
        pytest.main([str(run_dir), "-q", "--no-header"], plugins=[collector])

        shutil.rmtree(run_dir)

    not_started = max(total_scenarios - collector.total, 0)
    if skipped or skipped_scenarios or not_started > 0:
        print("--- Причины незапуска ---")
        if skipped:
            print("Feature файлы (целиком):")
            for source, reason in skipped:
                print(f"- {source} ({reason})")
        if skipped_scenarios:
            print("Сценарии:")
            for scenario_name, reason in skipped_scenarios:
                print(f"- {scenario_name} ({reason})")
        if not (skipped or skipped_scenarios):
            print("Причины не определены: нет данных о пропусках.")
        print("-" * 30)
    if collector.failures:
        print("--- Причины падений ---")
        for nodeid, details in collector.failures:
            print(f"- {nodeid}")
            print(details)
            print("-" * 30)

    # Вывод метрик в самом конце, чтобы не ломать downstream-парсинг.
    print("\n" + "="*30)
    print("ИТОГОВЫЕ МЕТРИКИ")
    print("="*30)
    print(f"Всего тестов:           {total_scenarios}")
    print(f"Запущено:               {collector.total}")
    print(f"Не запущено:            {not_started}")
    print(f"Пройдено:               {collector.passed}")
    print(f"Провалено:              {collector.failed}")
    print(f"Пропущено (внутри pytest): {collector.skipped}")

    if total_scenarios > 0:
        pass_rate = (collector.passed / total_scenarios) * 100
        print(f"Pass Rate:     {pass_rate:.2f}%")
    else:
        print("Тесты не были найдены или запущены.")
    print("="*30)

if __name__ == "__main__":
    main()
