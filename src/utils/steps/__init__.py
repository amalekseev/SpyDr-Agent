"""BDD steps: parsing, indexing, validation, and rendering.

Public API
----------
Singleton access (lazy-loaded from step source files):
    get_steps_index, get_steps_data, get_step_def, reload_steps

Indexing (async, PGVector):
    reindex_steps

Validation:
    validate_step_params, requires_docstring, requires_datatable

Parsing primitives (re-exported from ``parser`` sub-module):
    PLACEHOLDER_RE, REGEX_NAMED_GROUP_RE, substitute_pattern

Rendering (re-exported from ``renderer`` sub-module):
    render_step_text
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.configs import global_config
from src.utils.docstring_lint import validate_docstring_content

from .catalog import build_steps_index, format_steps_for_prompt
from .indexer import reindex_steps
from .parser import (
    PLACEHOLDER_RE,
    REGEX_NAMED_GROUP_RE,
    parse_steps_directory,
    substitute_pattern,
)
from .renderer import render_step_text

__all__ = [
    # Singleton
    "get_step_def",
    "get_steps_data",
    "get_steps_index",
    "reload_steps",
    # Indexing
    "reindex_steps",
    # Validation
    "requires_datatable",
    "requires_docstring",
    "validate_step_params",
    # Parser re-exports
    "PLACEHOLDER_RE",
    "REGEX_NAMED_GROUP_RE",
    "substitute_pattern",
    # Catalog re-exports
    "build_steps_index",
    "format_steps_for_prompt",
    # Renderer re-exports
    "render_step_text",
]

# ---------------------------------------------------------------------------
# Singleton: lazy-loaded step index
# ---------------------------------------------------------------------------

_steps_data: dict[str, Any] | None = None
_steps_index: dict[str, dict[str, Any]] | None = None


def _resolve_steps_dir() -> Path:
    """Return the absolute path to the BDD step-definition directory.

    Uses ``steps_dir`` from ``config.yml`` (relative to project root) or
    falls back to ``gherkin/tests/steps``.
    """
    configured = global_config.get("steps_dir", "gherkin/tests/steps")
    steps_dir = Path(configured)
    if not steps_dir.is_absolute():
        project_root = Path(__file__).resolve().parents[3]
        steps_dir = project_root / steps_dir
    return steps_dir


def _ensure_loaded() -> None:
    global _steps_data, _steps_index
    if _steps_index is not None:
        return
    steps_dir = _resolve_steps_dir()
    _steps_data = parse_steps_directory(str(steps_dir))
    _steps_index = build_steps_index(_steps_data)


def reload_steps() -> None:
    """Force re-parse of step source files (e.g. after directory changes)."""
    global _steps_data, _steps_index
    _steps_data = None
    _steps_index = None
    _ensure_loaded()


def get_steps_data() -> dict[str, Any]:
    """Return the full parsed steps dictionary."""
    _ensure_loaded()
    assert _steps_data is not None
    return _steps_data


def get_steps_index() -> dict[str, dict[str, Any]]:
    """Return the step-id → step-def lookup index."""
    _ensure_loaded()
    assert _steps_index is not None
    return _steps_index


def get_step_def(step_id: str) -> dict[str, Any] | None:
    """Look up a single step definition by its id."""
    return get_steps_index().get(step_id)


# ---------------------------------------------------------------------------
# Step-definition predicates
# ---------------------------------------------------------------------------


def requires_docstring(step_def: dict[str, Any]) -> bool:
    """Check whether a step requires a docstring payload."""
    explicit = step_def.get("requires_docstring")
    if isinstance(explicit, bool):
        return explicit
    return str(step_def.get("pattern", "")).rstrip().endswith(":")


def requires_datatable(step_def: dict[str, Any]) -> bool:
    """Check whether a step requires a datatable payload."""
    explicit = step_def.get("requires_datatable")
    if isinstance(explicit, bool):
        return explicit
    return False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_step_params(
    step_def: dict[str, Any],
    params: dict[str, Any],
    docstring: str | None,
    datatable: list[list[str]] | None,
    docstring_lang: str | None = None,
) -> list[str]:
    """Validate params / docstring / datatable against a step definition.

    Returns a list of error strings (empty when valid).
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
        supported_langs = list(
            global_config.get("docstring", {}).get("supported_langs", [])
        )
        if docstring_lang.strip().lower() not in [s.lower() for s in supported_langs]:
            errors.append(
                f"docstring_lang '{docstring_lang}' не в списке поддерживаемых: "
                f"{supported_langs}."
            )
        elif not (docstring and docstring.strip()):
            errors.append("Указан docstring_lang, но docstring пустой.")
        else:
            errors.extend(validate_docstring_content(docstring, docstring_lang))

    return errors
