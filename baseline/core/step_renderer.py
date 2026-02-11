"""Rendering Gherkin from strict step_id plan with validations."""

from __future__ import annotations

from typing import Any

from .agent_protocol import FeaturePlan
from .step_parser import PLACEHOLDER_RE


def render_feature_from_plan(
    *, feature_plan: FeaturePlan, steps_index: dict[str, dict[str, Any]]
) -> tuple[str, dict[str, int]]:
    """Render feature text from validated plan and step dictionary."""
    lines: list[str] = []
    metrics = {
        "rag_steps_total": 0,
        "rag_validation_errors": 0,
        "rag_unresolved_steps": 0,
    }

    if feature_plan.tags:
        lines.append(" ".join(feature_plan.tags))
    lines.append(f"Feature: {feature_plan.title}")
    lines.append("")

    for scenario in feature_plan.scenarios:
        if scenario.tags:
            lines.append("  " + " ".join(scenario.tags))
        lines.append(f"  Scenario: {scenario.name}")

        for chosen_step in scenario.steps:
            metrics["rag_steps_total"] += 1
            step_def = steps_index.get(chosen_step.step_id)
            if not step_def:
                metrics["rag_unresolved_steps"] += 1
                raise ValueError(f"Шаг с id '{chosen_step.step_id}' не найден в каталоге.")
            try:
                step_text = _render_step_text(
                    pattern=str(step_def.get("pattern", "")),
                    placeholders=step_def.get("placeholders", []),
                    params=chosen_step.params,
                )
            except ValueError:
                metrics["rag_validation_errors"] += 1
                raise
            lines.append(f"    {chosen_step.keyword} {step_text}")
            requires_docstring = _requires_docstring(step_def=step_def)
            if requires_docstring:
                if not chosen_step.docstring or not chosen_step.docstring.strip():
                    metrics["rag_validation_errors"] += 1
                    raise ValueError(
                        f"Шаг '{chosen_step.step_id}' требует docstring (по сигнатуре step-функции/паттерну)."
                    )
                lines.extend(_render_docstring_block(chosen_step.docstring))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n", metrics


def _render_step_text(*, pattern: str, placeholders: list[dict[str, Any]], params: dict[str, Any]) -> str:
    """Render one step pattern by strict placeholder replacement."""
    expected = [str(item.get("name")) for item in placeholders if item.get("name")]
    missing = [name for name in expected if name not in params]
    extra = [name for name in params.keys() if name not in expected]
    if missing:
        raise ValueError(f"Отсутствуют параметры для плейсхолдеров: {missing}")
    if extra:
        raise ValueError(f"Переданы лишние параметры: {extra}")

    def replace(match) -> str:
        key = match.group("name")
        return _format_param_value(params[key])

    rendered = PLACEHOLDER_RE.sub(replace, pattern)
    return rendered


def _format_param_value(value: Any) -> str:
    """Convert parameter value to Gherkin inline representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _requires_docstring(*, step_def: dict[str, Any]) -> bool:
    """Detect if step must provide multiline docstring payload."""
    explicit = step_def.get("requires_docstring")
    if isinstance(explicit, bool):
        return explicit
    step_pattern = str(step_def.get("pattern", ""))
    return step_pattern.rstrip().endswith(":")


def _render_docstring_block(docstring: str) -> list[str]:
    """Render a Gherkin triple-quoted block with step indentation."""
    lines = ['      """']
    for raw_line in docstring.splitlines():
        lines.append(f"      {raw_line}" if raw_line else "      ")
    lines.append('      """')
    return lines

