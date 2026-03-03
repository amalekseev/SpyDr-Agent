"""Steps catalog: in-memory index and prompt formatting."""

from __future__ import annotations

from typing import Any


def build_steps_index(steps_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a fast lookup map ``step_id → step_dict``."""
    index: dict[str, dict[str, Any]] = {}
    for step in steps_data.get("steps", []):
        step_id = step.get("step_id")
        if isinstance(step_id, str) and step_id:
            index[step_id] = step
    return index


def format_steps_for_prompt(steps_data: dict[str, Any]) -> str:
    """Format parsed steps into a prompt-friendly catalog string."""
    lines: list[str] = [
        "ДОСТУПНЫЕ ШАГИ:",
        f"Всего шагов: {steps_data['total_steps']}",
        "",
    ]

    by_type: dict[str, list[dict[str, Any]]] = {"given": [], "when": [], "then": []}
    for step in steps_data.get("steps", []):
        step_types = step.get("type", "")
        if isinstance(step_types, str):
            step_types = [step_types]
        for t in step_types:
            bucket = by_type.get(str(t).lower())
            if bucket is not None:
                bucket.append(step)

    _SECTIONS = [
        ("given", "=== GIVEN (предусловия) ==="),
        ("when", "=== WHEN (действия) ==="),
        ("then", "=== THEN (проверки) ==="),
    ]
    for type_key, header in _SECTIONS:
        lines.append(header)
        for step in by_type[type_key]:
            pattern = step.get("pattern", "")
            docstring = step.get("docstring", "")
            keyword = type_key.capitalize()
            suffix = f"  # {docstring}" if docstring else ""
            lines.append(f"  {keyword} {pattern}{suffix}")
        lines.append("")

    return "\n".join(lines)
