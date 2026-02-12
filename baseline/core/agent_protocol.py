"""Contracts for strict ID-only response from LLM agent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


VALID_KEYWORDS = {"Given", "When", "Then", "And", "But"}
KEYWORD_ALIASES = {
    "given": "Given",
    "when": "When",
    "then": "Then",
    "and": "And",
    "but": "But",
    # Common Russian variants that some models output.
    "допустим": "Given",
    "если": "Given",
    "когда": "When",
    "то": "Then",
    "и": "And",
    "но": "But",
}


@dataclass
class StepChoice:
    """Step selection made by the agent."""

    keyword: str
    step_id: str
    params: dict[str, Any]
    docstring: str | None = None


@dataclass
class ScenarioPlan:
    """Scenario representation in strict JSON format."""

    name: str
    tags: list[str]
    steps: list[StepChoice]


@dataclass
class FeaturePlan:
    """Feature representation in strict JSON format."""

    title: str
    tags: list[str]
    scenarios: list[ScenarioPlan]


def parse_agent_response(content: str) -> FeaturePlan:
    """Parse and validate strict JSON from model response."""
    raw = _strip_code_fences(content.strip())
    data = json.loads(raw)

    title = str(data.get("feature", "")).strip()
    if not title:
        raise ValueError("Ответ агента не содержит корректное поле feature.")
    feature_tags = _normalize_tags(data.get("tags", []))
    scenarios_data = data.get("scenarios")
    if not isinstance(scenarios_data, list) or not scenarios_data:
        raise ValueError("Ответ агента должен содержать непустой список scenarios.")

    scenarios: list[ScenarioPlan] = []
    for idx, scenario in enumerate(scenarios_data, start=1):
        scenario_name = str(scenario.get("name", "")).strip()
        if not scenario_name:
            raise ValueError(f"Сценарий #{idx}: отсутствует name.")
        scenario_tags = _normalize_tags(scenario.get("tags", []))
        steps_data = scenario.get("steps")
        if not isinstance(steps_data, list) or not steps_data:
            raise ValueError(f"Сценарий '{scenario_name}': steps должен быть непустым списком.")
        steps: list[StepChoice] = []
        for step_idx, step in enumerate(steps_data, start=1):
            raw_keyword = str(step.get("keyword", "")).strip()
            keyword = _normalize_keyword(raw_keyword)
            if keyword not in VALID_KEYWORDS:
                raise ValueError(
                    f"Сценарий '{scenario_name}', шаг #{step_idx}: keyword={raw_keyword!r} "
                    f"невалиден; ожидается одно из {sorted(VALID_KEYWORDS)}."
                )
            step_id = str(step.get("step_id", "")).strip()
            if not step_id:
                raise ValueError(f"Сценарий '{scenario_name}', шаг #{step_idx}: отсутствует step_id.")
            params = step.get("params", {})
            if not isinstance(params, dict):
                raise ValueError(f"Сценарий '{scenario_name}', шаг #{step_idx}: params должен быть объектом.")
            raw_docstring = step.get("docstring")
            if raw_docstring is not None and not isinstance(raw_docstring, str):
                raise ValueError(
                    f"Сценарий '{scenario_name}', шаг #{step_idx}: docstring должен быть строкой или null."
                )
            docstring = raw_docstring if isinstance(raw_docstring, str) else None
            steps.append(StepChoice(keyword=keyword, step_id=step_id, params=params, docstring=docstring))
        scenarios.append(ScenarioPlan(name=scenario_name, tags=scenario_tags, steps=steps))

    return FeaturePlan(title=title, tags=feature_tags, scenarios=scenarios)


def _strip_code_fences(content: str) -> str:
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _normalize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    tags: list[str] = []
    for item in raw_tags:
        tag = str(item).strip()
        if not tag:
            continue
        if not tag.startswith("@"):
            tag = f"@{tag}"
        tags.append(tag)
    return tags


def _normalize_keyword(raw_keyword: str) -> str:
    """Normalize model keyword output to strict Gherkin keyword set."""
    cleaned = raw_keyword.strip().strip(":")
    if not cleaned:
        return ""
    alias = KEYWORD_ALIASES.get(cleaned.lower())
    if alias:
        return alias
    return cleaned

