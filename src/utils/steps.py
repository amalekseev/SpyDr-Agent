"""Singleton steps index loaded from steps.json at import time."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from baseline.core.steps_catalog import load_steps, build_steps_index
from baseline.core.constants import DEFAULT_STEPS_FILE
from src.configs import global_config
from src.utils.docstring_lint import validate_docstring_content

PLACEHOLDER_RE = re.compile(
    r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}"
)

_steps_data: dict[str, Any] | None = None
_steps_index: dict[str, dict[str, Any]] | None = None


def _ensure_loaded() -> None:
    global _steps_data, _steps_index
    if _steps_index is not None:
        return
    steps_file = Path.cwd() / DEFAULT_STEPS_FILE
    _steps_data = load_steps(steps_file)
    _steps_index = build_steps_index(_steps_data)


def get_steps_index() -> dict[str, dict[str, Any]]:
    _ensure_loaded()
    assert _steps_index is not None
    return _steps_index


def get_step_def(step_id: str) -> dict[str, Any] | None:
    return get_steps_index().get(step_id)


def requires_docstring(step_def: dict[str, Any]) -> bool:
    explicit = step_def.get("requires_docstring")
    if isinstance(explicit, bool):
        return explicit
    return str(step_def.get("pattern", "")).rstrip().endswith(":")


def requires_datatable(step_def: dict[str, Any]) -> bool:
    explicit = step_def.get("requires_datatable")
    if isinstance(explicit, bool):
        return explicit
    return False


def validate_step_params(
    step_def: dict[str, Any],
    params: dict[str, Any],
    docstring: str | None,
    datatable: list[list[str]] | None,
    docstring_lang: str | None = None,
) -> list[str]:
    """Validate params/docstring/datatable against step definition.

    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []
    placeholders = step_def.get("placeholders", [])
    expected = [str(p.get("name")) for p in placeholders if p.get("name")]

    missing = [n for n in expected if n not in params]
    extra = [n for n in params if n not in expected]
    if missing:
        errors.append(f"Отсутствуют параметры: {missing}")
    if extra:
        errors.append(f"Лишние параметры: {extra}")

    if requires_docstring(step_def) and not (docstring and docstring.strip()):
        errors.append(
            f"Шаг '{step_def.get('step_id')}' требует docstring "
            f"(pattern заканчивается на ':' или requires_docstring=true)."
        )
    if requires_datatable(step_def) and not datatable:
        errors.append(
            f"Шаг '{step_def.get('step_id')}' требует datatable "
            f"(requires_datatable=true)."
        )

    if docstring_lang:
        supported_langs = list(global_config.get("docstring", {}).get("supported_langs", []))
        if docstring_lang.strip().lower() not in [s.lower() for s in supported_langs]:
            errors.append(
                f"docstring_lang '{docstring_lang}' не в списке поддерживаемых: {supported_langs}."
            )
        elif not (docstring and docstring.strip()):
            errors.append("Указан docstring_lang, но docstring пустой.")
        else:
            errors.extend(validate_docstring_content(docstring, docstring_lang))

    return errors
