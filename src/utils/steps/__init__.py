"""BDD steps: parsing, indexing, validation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.configs import global_config
from src.utils.docstring_lint import validate_docstring_content

from .catalog import build_steps_index
from .parser import parse_steps_directory, substitute_pattern

__all__ = [
    "get_steps_index",
    "reload_steps",
    "reindex_steps",
    "requires_datatable",
    "requires_docstring",
    "validate_step_params",
    "substitute_pattern",
    "get_custom_collection_name",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default step index (singleton, lazy-loaded)
# ---------------------------------------------------------------------------

_steps_data: dict[str, Any] | None = None
_steps_index: dict[str, dict[str, Any]] | None = None


def _resolve_steps_dir() -> Path:
    configured = global_config.get("steps_dir", "gherkin/tests/steps")
    steps_dir = Path(configured)
    if not steps_dir.is_absolute():
        steps_dir = Path(__file__).resolve().parents[3] / steps_dir
    return steps_dir


def _ensure_loaded() -> None:
    global _steps_data, _steps_index
    if _steps_index is not None:
        return
    _steps_data = parse_steps_directory(str(_resolve_steps_dir()))
    _steps_index = build_steps_index(_steps_data)


def reload_steps() -> None:
    global _steps_data, _steps_index
    _steps_data = None
    _steps_index = None
    _ensure_loaded()


# ---------------------------------------------------------------------------
# Per-project helpers (config → path / collection name)
# ---------------------------------------------------------------------------


def _resolve_custom_steps_dir(project_id: str) -> Path | None:
    projects = global_config.get("projects") or {}
    cfg = projects.get(project_id)
    if not cfg:
        return None
    raw = cfg.get("custom_steps_dir")
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_absolute() else Path(__file__).resolve().parents[3] / p


def get_custom_collection_name(project_id: str) -> str:
    return f"{global_config.rag.steps.collection_name}_custom_{project_id}"


# ---------------------------------------------------------------------------
# Index access
# ---------------------------------------------------------------------------


def get_steps_index() -> dict[str, dict[str, Any]]:
    _ensure_loaded()
    assert _steps_index is not None
    return _steps_index



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
