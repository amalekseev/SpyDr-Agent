"""Steps catalog: in-memory index."""

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
