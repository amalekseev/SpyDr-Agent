"""Gherkin feature-text rendering from step plans.

Works with any step-choice objects that expose ``step_id``, ``keyword``,
``params``, ``docstring``, and ``datatable`` attributes (both Pydantic
models from ``src.agents.models`` and plain dataclasses satisfy this).
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from .parser import substitute_pattern


# ---------------------------------------------------------------------------
# Structural protocols — accept any object with the right attributes
# ---------------------------------------------------------------------------


class StepLike(Protocol):
    step_id: str
    keyword: str
    params: dict[str, Any]
    docstring: str | None
    datatable: list[list[str]] | None


class ScenarioLike(Protocol):
    name: str
    tags: list[str]
    steps: Sequence[StepLike]
    examples: list[list[str]] | None


class FeatureLike(Protocol):
    title: str
    tags: list[str]
    scenarios: Sequence[ScenarioLike]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_feature_from_plan(
    *,
    feature_plan: FeatureLike,
    steps_index: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, int]]:
    """Render Gherkin feature text from a validated plan and step index.

    Returns ``(feature_text, metrics_dict)``.
    """
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
        has_examples = scenario.examples and len(scenario.examples) >= 2
        scenario_keyword = "Scenario Outline" if has_examples else "Scenario"

        if scenario.tags:
            lines.append("  " + " ".join(scenario.tags))
        lines.append(f"  {scenario_keyword}: {scenario.name}")

        for chosen_step in scenario.steps:
            metrics["rag_steps_total"] += 1
            step_def = steps_index.get(chosen_step.step_id)
            if not step_def:
                metrics["rag_unresolved_steps"] += 1
                raise ValueError(
                    f"Шаг с id '{chosen_step.step_id}' не найден в каталоге."
                )
            try:
                step_text = render_step_text(
                    pattern=str(step_def.get("pattern", "")),
                    placeholders=step_def.get("placeholders", []),
                    params=chosen_step.params,
                    parser_kind=step_def.get("parser_kind", "parse"),
                )
            except ValueError:
                metrics["rag_validation_errors"] += 1
                raise
            lines.append(f"    {chosen_step.keyword} {step_text}")

            needs_docstring = _requires_docstring(step_def)
            needs_datatable = _requires_datatable(step_def)

            if needs_datatable:
                if chosen_step.datatable:
                    lines.extend(_render_datatable_block(chosen_step.datatable))
                elif chosen_step.docstring and chosen_step.docstring.strip():
                    parsed = _parse_datatable_from_string(chosen_step.docstring)
                    if parsed:
                        lines.extend(_render_datatable_block(parsed))
                    else:
                        lines.extend(_render_docstring_block(chosen_step.docstring))
                else:
                    metrics["rag_validation_errors"] += 1
                    raise ValueError(
                        f"Шаг '{chosen_step.step_id}' требует datatable "
                        f"(по сигнатуре step-функции). Обязательно передай datatable."
                    )
            elif needs_docstring:
                if chosen_step.docstring and chosen_step.docstring.strip():
                    lines.extend(_render_docstring_block(chosen_step.docstring))
                else:
                    metrics["rag_validation_errors"] += 1
                    raise ValueError(
                        f"Шаг '{chosen_step.step_id}' требует docstring "
                        f"(по сигнатуре step-функции/паттерну). Обязательно передай docstring."
                    )

        if has_examples:
            lines.append("")
            lines.append("    Examples:")
            lines.extend(_render_datatable_block(scenario.examples, indent="      "))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n", metrics


# ---------------------------------------------------------------------------
# Step text rendering
# ---------------------------------------------------------------------------


def render_step_text(
    *,
    pattern: str,
    placeholders: list[dict[str, Any]],
    params: dict[str, Any],
    parser_kind: str = "parse",
) -> str:
    """Render one step pattern by strict placeholder replacement."""
    expected = [str(item.get("name")) for item in placeholders if item.get("name")]
    missing = [name for name in expected if name not in params]
    extra = [name for name in params if name not in expected]
    if missing:
        raise ValueError(f"Отсутствуют параметры для плейсхолдеров: {missing}")
    if extra:
        raise ValueError(f"Переданы лишние параметры: {extra}")

    return substitute_pattern(pattern, params, parser_kind)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _requires_docstring(step_def: dict[str, Any]) -> bool:
    explicit = step_def.get("requires_docstring")
    if isinstance(explicit, bool):
        return explicit
    return str(step_def.get("pattern", "")).rstrip().endswith(":")


def _requires_datatable(step_def: dict[str, Any]) -> bool:
    explicit = step_def.get("requires_datatable")
    if isinstance(explicit, bool):
        return explicit
    return False


def _render_docstring_block(docstring: str) -> list[str]:
    """Render a Gherkin triple-quoted block with step indentation."""
    lines = ['      """']
    for raw_line in docstring.splitlines():
        lines.append(f"      {raw_line}" if raw_line else "      ")
    lines.append('      """')
    return lines


def _render_datatable_block(datatable: list[list[str]], indent: str = "      ") -> list[str]:
    """Render a Gherkin datatable (pipe-delimited) with step indentation."""
    if not datatable:
        return []

    num_cols = max(len(row) for row in datatable)
    col_widths = [0] * num_cols
    for row in datatable:
        for col_idx, cell in enumerate(row):
            col_widths[col_idx] = max(col_widths[col_idx], len(cell))

    lines: list[str] = []
    for row in datatable:
        cells = []
        for col_idx in range(num_cols):
            cell = row[col_idx] if col_idx < len(row) else ""
            cells.append(f" {cell:<{col_widths[col_idx]}} ")
        lines.append(f"{indent}|" + "|".join(cells) + "|")
    return lines


def _parse_datatable_from_string(text: str) -> list[list[str]] | None:
    """Try to parse pipe-delimited datatable from a plain string."""
    rows: list[list[str]] = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return None
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows if rows else None
