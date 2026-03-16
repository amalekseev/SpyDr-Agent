"""Rendering helpers for Gherkin feature files.

All functions work with ``found_steps`` — the step definitions accumulated
in ``AgentState.found_steps`` by the ``search_steps`` tool at runtime.
No dependency on the static ``steps_index`` / ``get_steps_index()`` from
``src.utils.steps``.
"""

from __future__ import annotations

import re
from typing import Any

from src.agents.models import ScenarioDraft, StepChoice

PLACEHOLDER_RE = re.compile(
    r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}"
)


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


# ------------------------------------------------------------------
# Low-level rendering
# ------------------------------------------------------------------

def render_step_text(
    *, pattern: str, placeholders: list[dict[str, Any]], params: dict[str, Any],
) -> str:
    """Substitute placeholders in a step pattern with actual param values."""
    def replace(match: re.Match) -> str:
        key = match.group("name")
        val = params.get(key)
        if isinstance(val, bool):
            return "true" if val else "false"
        return "" if val is None else str(val)
    return PLACEHOLDER_RE.sub(replace, pattern)


def render_step_preview(step_def: dict[str, Any], step: StepChoice) -> str:
    """Human-readable preview of a single step (keyword + text + docstring/datatable)."""
    text = render_step_text(
        pattern=str(step_def.get("pattern", "")),
        placeholders=step_def.get("placeholders", []),
        params=step.params,
    )
    preview = f"{step.keyword} {text}"
    if step.docstring:
        lang = step.docstring_lang
        opener = f'"""{(lang or "")}' if lang else '"""'
        preview += f"\n      {opener}\n"
        for line in step.docstring.splitlines():
            preview += f"      {line}\n" if line else "      \n"
        preview += '      """'
    if step.datatable:
        for row in step.datatable:
            preview += "\n      | " + " | ".join(row) + " |"
    return preview


def render_docstring_block(
    docstring: str, lang: str | None = None, indent: str = "      ",
) -> list[str]:
    opener = f'"""{lang}' if lang else '"""'
    lines = [f"{indent}{opener}"]
    for raw_line in docstring.splitlines():
        lines.append(f"{indent}{raw_line}" if raw_line else indent)
    lines.append(f'{indent}"""')
    return lines


def render_datatable_block(
    datatable: list[list[str]], indent: str = "      ",
) -> list[str]:
    if not datatable:
        return []
    num_cols = max(len(row) for row in datatable)
    col_widths = [0] * num_cols
    for row in datatable:
        for ci, cell in enumerate(row):
            col_widths[ci] = max(col_widths[ci], len(cell))
    lines: list[str] = []
    for row in datatable:
        cells = []
        for ci in range(num_cols):
            cell = row[ci] if ci < len(row) else ""
            cells.append(f" {cell:<{col_widths[ci]}} ")
        lines.append(f"{indent}|" + "|".join(cells) + "|")
    return lines


def parse_datatable_from_string(text: str) -> list[list[str]] | None:
    rows: list[list[str]] = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return None
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows if rows else None


def normalize_keyword(raw: str) -> str | None:
    aliases = {
        "given": "Given", "when": "When", "then": "Then",
        "and": "And", "but": "But",
        "допустим": "Given", "если": "Given",
        "когда": "When", "то": "Then", "и": "And", "но": "But",
    }
    cleaned = raw.strip().strip(":")
    if cleaned in {"Given", "When", "Then", "And", "But"}:
        return cleaned
    return aliases.get(cleaned.lower())


# ------------------------------------------------------------------
# Feature-level rendering
# ------------------------------------------------------------------

def _render_step_into(
    lines: list[str],
    step: StepChoice,
    found_steps: dict[str, dict[str, Any]],
    indent: str = "    ",
) -> None:
    step_def = found_steps[step.step_id]
    step_text = render_step_text(
        pattern=str(step_def.get("pattern", "")),
        placeholders=step_def.get("placeholders", []),
        params=step.params,
    )
    lines.append(f"{indent}{step.keyword} {step_text}")

    doc_indent = indent + "  "
    if _requires_datatable(step_def):
        if step.datatable:
            lines.extend(render_datatable_block(step.datatable, doc_indent))
        elif step.docstring and step.docstring.strip():
            parsed = parse_datatable_from_string(step.docstring)
            if parsed:
                lines.extend(render_datatable_block(parsed, doc_indent))
            else:
                lines.extend(render_docstring_block(step.docstring, step.docstring_lang, doc_indent))
    elif _requires_docstring(step_def):
        if step.docstring and step.docstring.strip():
            lines.extend(render_docstring_block(step.docstring, step.docstring_lang, doc_indent))


def render_feature(
    title: str,
    tags: list[str],
    background_steps: list[StepChoice],
    scenarios: list[ScenarioDraft],
    found_steps: dict[str, dict[str, Any]],
) -> str:
    """Render a complete Gherkin feature file from state components.

    ``found_steps`` is the ``AgentState.found_steps`` dict mapping
    ``step_id`` -> step definition dict.
    """
    lines: list[str] = []
    if tags:
        lines.append(" ".join(tags))
    lines.append(f"Feature: {title}")
    lines.append("")

    if background_steps:
        lines.append("  Background:")
        for step in background_steps:
            _render_step_into(lines, step, found_steps, indent="    ")
        lines.append("")

    for scenario in scenarios:
        has_examples = scenario.examples and len(scenario.examples) >= 2
        scenario_keyword = "Scenario Outline" if has_examples else "Scenario"

        if scenario.tags:
            lines.append("  " + " ".join(scenario.tags))
        lines.append(f"  {scenario_keyword}: {scenario.name}")

        for step in scenario.steps:
            _render_step_into(lines, step, found_steps, indent="    ")

        if has_examples:
            lines.append("")
            lines.append("    Examples:")
            lines.extend(render_datatable_block(scenario.examples, indent="      "))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_feature_from_state(state: dict[str, Any]) -> str | None:
    """Convenience: render feature directly from an AgentState dict.

    Returns ``None`` if the feature cannot be rendered (no title or missing step defs).
    """
    title: str = state.get("feature_title", "")
    if not title:
        return None
    tags: list[str] = state.get("feature_tags", [])
    bg_steps: list[StepChoice] = state.get("background_steps") or []
    scenarios: list[ScenarioDraft] = state.get("scenarios") or []
    found_steps: dict[str, dict[str, Any]] = state.get("found_steps") or {}

    try:
        return render_feature(title, tags, bg_steps, scenarios, found_steps)
    except Exception:
        return None
