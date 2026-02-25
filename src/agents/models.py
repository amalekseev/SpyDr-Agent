from __future__ import annotations

from typing import Annotated, Any, Literal

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


def _last_value(existing: Any, new: Any) -> Any:
    """Reducer: always keep the latest value. Allows concurrent tool writes."""
    return new


def _merge_dicts(existing: dict, new: dict) -> dict:
    """Reducer: shallow-merge dicts so parallel writes accumulate keys."""
    if existing is None:
        return new or {}
    if new is None:
        return existing
    return {**existing, **new}


class StepChoice(BaseModel):
    keyword: Literal["Given", "When", "Then", "And", "But"]
    step_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    docstring: str | None = None
    docstring_lang: str | None = None
    datatable: list[list[str]] | None = None


class ScenarioDraft(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)
    steps: list[StepChoice] = Field(default_factory=list)


class AgentState(MessagesState):
    feature_title: Annotated[str, _last_value]
    feature_tags: Annotated[list[str], _last_value]
    background_steps: Annotated[list[StepChoice], _last_value]
    scenarios: Annotated[list[ScenarioDraft], _last_value]
    found_steps: Annotated[dict[str, dict[str, Any]], _merge_dicts]
    found_docs: Annotated[dict[str, dict[str, Any]], _merge_dicts]
