"""Backward-compatible re-exports from ``src.utils.steps.renderer``.

The canonical implementation now lives in ``src/utils/steps/renderer.py``.
This module exists so that the baseline pipeline continues to work.
"""

from src.utils.steps.renderer import (  # noqa: F401
    render_feature_from_plan,
    render_step_text,
)
