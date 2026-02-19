"""Loading and prompt formatting for available BDD steps."""

import json
import re
from pathlib import Path
from typing import Any

from .step_parser import build_step_id, extract_placeholders

STEP_FUNC_RE = re.compile(r"^\s*def\s+(\w+)\s*\((.*?)\)\s*:")


def load_steps(steps_file: Path) -> dict[str, Any]:
    """Load steps from JSON file and validate required shape."""
    if not steps_file.exists():
        raise FileNotFoundError(f"Файл шагов не найден: {steps_file}")

    data = json.loads(steps_file.read_text(encoding="utf-8"))
    steps = data.get("steps", [])

    counters = {"given": 0, "when": 0, "then": 0}
    step_args_index = _load_step_signature_index()
    for step in steps:
        step_types = step.get("type", "")
        if isinstance(step_types, str):
            step_types = [step_types]

        for t in step_types:
            t = t.lower()
            if t in counters:
                counters[t] += 1

        if not step.get("placeholders"):
            step["placeholders"] = extract_placeholders(str(step.get("pattern", "")))
        if not step.get("step_id"):
            step["step_id"] = build_step_id(
                step_type=step.get("type", "unknown"),
                pattern=str(step.get("pattern", "")),
                source_file=str(step.get("source_file", "")),
                function_name=step.get("function_name"),
            )
        _annotate_step_payload_requirements(step=step, step_args_index=step_args_index)

    data["steps"] = steps
    data["total_steps"] = len(steps)
    data["steps_by_type"] = counters
    return data


def _load_step_signature_index() -> dict[tuple[str, str], set[str]]:
    """Build index (source_file, function_name) -> normalized argument names."""
    root = Path(__file__).resolve().parents[2]
    steps_dir = root / "gherkin" / "tests" / "steps"
    index: dict[tuple[str, str], set[str]] = {}
    if not steps_dir.exists():
        return index

    for step_file in steps_dir.glob("*.py"):
        try:
            lines = step_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            match = STEP_FUNC_RE.match(line)
            if not match:
                continue
            function_name = match.group(1)
            raw_args = match.group(2)
            args = {
                part.strip().split("=", maxsplit=1)[0].strip()
                for part in raw_args.split(",")
                if part.strip()
            }
            index[(step_file.name, function_name)] = args
    return index


def _annotate_step_payload_requirements(
    *, step: dict[str, Any], step_args_index: dict[tuple[str, str], set[str]]
) -> None:
    """Annotate whether a step requires multiline payload objects."""
    source_file = str(step.get("source_file", ""))
    function_name = str(step.get("function_name", ""))
    args = step_args_index.get((source_file, function_name))
    if not args:
        return
    step["requires_docstring"] = "docstring" in args
    step["requires_datatable"] = "datatable" in args


def build_steps_index(steps_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build fast lookup map by step_id."""
    index: dict[str, dict[str, Any]] = {}
    for step in steps_data.get("steps", []):
        step_id = step.get("step_id")
        if isinstance(step_id, str) and step_id:
            index[step_id] = step
    return index


def format_steps_for_prompt(steps_data: dict[str, Any]) -> str:
    """Format parsed steps into a prompt-friendly catalog."""
    lines: list[str] = []
    lines.append("ДОСТУПНЫЕ ШАГИ:")
    lines.append(f"Всего шагов: {steps_data['total_steps']}")
    lines.append("")

    steps_by_type: dict[str, list[dict[str, Any]]] = {"given": [], "when": [], "then": []}
    for step in steps_data.get("steps", []):
        step_types = step.get("type", "")
        if isinstance(step_types, str):
            step_types = [step_types]

        for t in step_types:
            t = str(t).lower()
            if t in steps_by_type:
                steps_by_type[t].append(step)

    lines.append("=== GIVEN (предусловия) ===")
    for step in steps_by_type["given"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        lines.append(f"  Given {pattern}" + (f"  # {docstring}" if docstring else ""))
    lines.append("")

    lines.append("=== WHEN (действия) ===")
    for step in steps_by_type["when"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        lines.append(f"  When {pattern}" + (f"  # {docstring}" if docstring else ""))
    lines.append("")

    lines.append("=== THEN (проверки) ===")
    for step in steps_by_type["then"]:
        pattern = step.get("pattern", "")
        docstring = step.get("docstring", "")
        lines.append(f"  Then {pattern}" + (f"  # {docstring}" if docstring else ""))

    return "\n".join(lines)
