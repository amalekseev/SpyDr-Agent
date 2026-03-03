"""Backward-compatible re-exports from ``src.utils.steps.catalog``.

The canonical implementation now lives in ``src/utils/steps/catalog.py``.
``load_steps`` is retained here for legacy CLI / pipeline support but is
no longer used by the interactive agent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.utils.steps.catalog import build_steps_index, format_steps_for_prompt  # noqa: F401
from src.utils.steps.parser import StepIdCounter, build_step_id, extract_placeholders


def load_steps(steps_file: Path) -> dict[str, Any]:
    """Load steps from a pre-generated JSON file (legacy path).

    The interactive agent no longer needs this — it parses source files
    directly via ``parse_steps_directory``.
    """
    if not steps_file.exists():
        raise FileNotFoundError(f"Файл шагов не найден: {steps_file}")

    data = json.loads(steps_file.read_text(encoding="utf-8"))
    steps = data.get("steps", [])

    counters = {"given": 0, "when": 0, "then": 0}
    id_counter = StepIdCounter()
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
            step["step_id"] = build_step_id(id_counter)

    data["steps"] = steps
    data["total_steps"] = len(steps)
    data["steps_by_type"] = counters
    return data
