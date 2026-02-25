from pathlib import Path

from langgraph.graph.state import CompiledStateGraph
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.agents import config
from src.agents.base import BaseAgent
from src.agents.models import AgentState
from src.agents.tools import ALL_TOOLS
from src.configs import global_config


class SpydrAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            config=config
        )

        self.memory = InMemorySaver()

        self.retry_middleware = ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0
        )

    def _build_graph(self) -> CompiledStateGraph:
        system_prompt = self._build_system_prompt()

        return create_agent(
            model=self.llm,
            middleware=[self.retry_middleware],
            tools=ALL_TOOLS,
            state_schema=AgentState,
            system_prompt=system_prompt,
            checkpointer=self.memory,
        )

    def _build_system_prompt(self) -> str:
        supported_langs = list(
            global_config.get("docstring", {}).get("supported_langs", [])
        )
        langs_str = ", ".join(supported_langs) if supported_langs else ""
        system_prompt = self._load_system_prompt().format(
            docstring_supported_langs=langs_str,
        )
        user_rules = self._load_user_rules()
        if user_rules:
            system_prompt += f"\n\n# Пользовательские правила\n\n{user_rules}"
        return system_prompt

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
        return prompt_path.read_text(encoding="utf-8")

    def _load_user_rules(self) -> str:
        rules_path = Path(__file__).resolve().parents[2] / "RULES.md"
        if not rules_path.exists():
            return ""
        content = rules_path.read_text(encoding="utf-8").strip()
        return content
