from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.config import get_config

from src.agents import config
from src.agents.base import BaseAgent, build_chat_model
from src.agents.few_shot_selector import FewShotSelector
from src.agents.models import AgentState
from src.agents.tools import ALL_TOOLS
from src.agents.validator import FeatureValidator
from src.configs import global_config
from src.utils.streaming import set_status, stream_text

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SpydrAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(config=config)

        self.memory = InMemorySaver()

        self.retry_middleware = ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        )

        val_cfg = config.get("validation", {})
        val_llm_params: dict[str, Any] = val_cfg.get("llm_params", config.get("llm_params", {}))
        val_llm = build_chat_model(val_llm_params)
        self._validator = FeatureValidator(llm=val_llm)
        self._default_max_iterations: int = val_cfg.get("max_iterations", 3)

        few_shots_dir = _PROJECT_ROOT / global_config.rag.few_shots.few_shots_dir
        self._few_shot_selector = FewShotSelector(few_shots_dir=few_shots_dir)

    def _build_graph(self) -> CompiledStateGraph:
        system_prompt = self._build_system_prompt()

        builder_agent = create_agent(
            model=self.llm,
            middleware=[self.retry_middleware],
            tools=ALL_TOOLS,
            state_schema=AgentState,
            system_prompt=system_prompt,
        )

        graph = StateGraph(AgentState)
        graph.add_node("select_few_shots", self._select_few_shots_node)
        graph.add_node("builder", builder_agent)
        graph.add_node("validate", self._validate_node)
        graph.add_node("inject_feedback", self._inject_feedback_node)

        graph.set_entry_point("select_few_shots")
        graph.add_edge("select_few_shots", "builder")
        graph.add_conditional_edges(
            "builder",
            self._route_after_builder,
            {"validate": "validate", "__end__": END},
        )
        graph.add_conditional_edges(
            "validate",
            self._route_after_validate,
            {"__end__": END, "inject_feedback": "inject_feedback"},
        )
        graph.add_edge("inject_feedback", "builder")

        return graph.compile(checkpointer=self.memory)

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    async def _select_few_shots_node(self, state: AgentState) -> dict[str, Any]:
        """Select relevant few-shot examples based on the user request."""
        user_request = self._extract_user_request(state)
        if not user_request:
            logger.warning("select_few_shots_node: no user request found")
            return {"selected_few_shots": []}

        set_status("Подбираю примеры…")
        selected = await self._few_shot_selector.select(user_request)
        logger.info(
            "select_few_shots_node: selected %d few-shot(s) for request: %s",
            len(selected), user_request[:120],
        )
        set_status(f"Подобрано {len(selected)} примеров")
        return {"selected_few_shots": selected}

    async def _validate_node(self, state: AgentState) -> dict[str, Any]:
        """Run the validator LLM against the current feature."""
        feature_text = self._validator.render_feature(state)
        if feature_text is None:
            logger.warning("validate_node: feature not renderable, skipping")
            return {"validation_iteration": state.get("validation_iteration", 0)}

        user_request = self._extract_user_request(state)
        iteration = state.get("validation_iteration", 0)

        set_status(f"Валидация feature (итерация {iteration + 1})…")
        few_shots = state.get("selected_few_shots", [])
        result = await self._validator.validate(feature_text, user_request, few_shots=few_shots)

        if result.is_valid:
            set_status("Валидация пройдена")
            stream_text("\n\nВалидация пройдена — feature соответствует запросу.")
        else:
            set_status(f"Валидация не пройдена (итерация {iteration + 1})")

        return {
            "validation_iteration": iteration,
            "validation_result_valid": result.is_valid,
            "validation_feedback": result.feedback,
        }

    async def _inject_feedback_node(self, state: AgentState) -> dict[str, Any]:
        """Increment iteration counter and inject validator feedback as a user message."""
        iteration = (state.get("validation_iteration", 0)) + 1
        feedback = state.get("validation_feedback", "")

        cfg = get_config()
        max_iter = cfg.get("configurable", {}).get(
            "max_validation_iterations", self._default_max_iterations
        )

        stream_text(
            f"\n\nВалидатор нашёл проблемы (итерация {iteration}/{max_iter}). Исправляю…"
        )

        feedback_msg = HumanMessage(
            content=(
                f"Валидатор feature нашёл проблемы. Исправь их, используя инструменты.\n\n"
                f"Фидбек валидатора:\n{feedback}"
            )
        )

        return {
            "validation_iteration": iteration,
            "messages": [feedback_msg],
        }

    # ------------------------------------------------------------------
    # Routing functions
    # ------------------------------------------------------------------

    @staticmethod
    def _route_after_builder(state: AgentState) -> str:
        """After builder finishes, decide whether to validate or end."""
        cfg = get_config()
        enabled = cfg.get("configurable", {}).get("validation_enabled", False)
        if not enabled:
            return "__end__"
        return "validate"

    def _route_after_validate(self, state: AgentState) -> str:
        """After validation, decide whether to end or loop back with feedback."""
        is_valid = state.get("validation_result_valid", True)
        if is_valid:
            return "__end__"

        iteration = state.get("validation_iteration", 0)
        cfg = get_config()
        max_iter = cfg.get("configurable", {}).get(
            "max_validation_iterations", self._default_max_iterations
        )

        if iteration >= max_iter:
            stream_text(
                f"\n\nДостигнут лимит итераций валидации ({max_iter}). "
                "Feature возвращается как есть."
            )
            return "__end__"

        return "inject_feedback"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_user_request(state: AgentState) -> str:
        """Extract the original user request from the first message."""
        messages = state.get("messages", [])
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "human":
                return msg.content
            if isinstance(msg, dict) and msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _build_system_prompt(self) -> str:
        supported_langs = list(
            global_config.get("docstring", {}).get("supported_langs", [])
        )
        langs_str = ", ".join(supported_langs) if supported_langs else ""
        system_prompt = self._load_system_prompt().format(
            docstring_supported_langs=langs_str,
        )

        docs_context = self._load_docs_context()
        if docs_context:
            system_prompt += f"\n\n# Контекст из документации проекта\n\n{docs_context}"

        user_rules = self._load_user_rules()
        if user_rules:
            system_prompt += f"\n\n# Пользовательские правила\n\n{user_rules}"

        return system_prompt

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
        return prompt_path.read_text()

    def _load_docs_context(self) -> str:
        prompts_dir = Path(__file__).parent / "prompts"
        parts = []
        for fname in ("docs_hooks.md", "docs_summary.md"):
            path = prompts_dir / fname
            if path.exists():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    parts.append(content)
        return "\n\n".join(parts)

    def _load_user_rules(self) -> str:
        rules_path = Path(__file__).resolve().parents[2] / "RULES.md"
        if not rules_path.exists():
            return ""
        content = rules_path.read_text().strip()
        return content
