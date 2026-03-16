"""Validation agent that reviews generated features against few-shot examples."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.utils import render_feature_from_state

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


class ValidationResult(BaseModel):
    """Structured output from the validator LLM."""

    is_valid: bool = Field(
        description="True если сгенерированный feature корректен и полностью соответствует запросу пользователя."
    )
    feedback: str = Field(
        default="",
        description="Если is_valid=False — конкретный, actionable фидбек: что именно не так и как исправить.",
    )


class FeatureValidator:
    """Validates a generated .feature against few-shot reference examples."""

    def __init__(
        self,
        llm: BaseChatModel,
    ) -> None:
        self._llm = llm.with_structured_output(ValidationResult)
        self._system_prompt = self._load_prompt()

    @staticmethod
    def _load_prompt() -> str:
        path = _PROMPTS_DIR / "validator_prompt.md"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def render_feature(state: dict[str, Any]) -> str | None:
        """Render the current feature from agent state.

        Uses ``found_steps`` from state — no dependency on the static steps index.
        Returns ``None`` if not renderable.
        """
        return render_feature_from_state(state)

    async def validate(
        self,
        feature_text: str,
        user_request: str,
        few_shots: list[dict[str, str]] | None = None,
    ) -> ValidationResult:
        """Validate a generated feature against few-shot examples.

        Args:
            feature_text: The rendered Gherkin feature text.
            user_request: The original user request.
            few_shots: Pre-selected few-shot examples from AgentState.
                Each dict has keys ``id``, ``file``, ``content``.
        """
        if few_shots is None:
            few_shots = []

        few_shots_block = ""
        if few_shots:
            parts = []
            for fs in few_shots:
                fname = fs.get("file", fs.get("id", "example"))
                content = fs.get("content", "")
                parts.append(f"### {fname}\n```gherkin\n{content}```")
            few_shots_block = (
                "## Эталонные примеры (few-shots)\n\n"
                + "\n\n".join(parts)
            )

        user_content = (
            f"## Запрос пользователя\n\n{user_request}\n\n"
            f"{few_shots_block}\n\n"
            f"## Сгенерированный Feature\n\n```gherkin\n{feature_text}```"
        )

        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=user_content),
        ]

        logger.info("FeatureValidator: calling LLM with %d few-shot examples", len(few_shots))
        result: ValidationResult = await self._llm.ainvoke(messages)
        logger.info("FeatureValidator: is_valid=%s", result.is_valid)
        return result
