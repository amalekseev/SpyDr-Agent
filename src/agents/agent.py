from pathlib import Path

from langgraph.graph.state import CompiledStateGraph
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.agents import config
from src.agents.base import BaseAgent
from src.agents.tools import search_steps

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
        base_prompt = self._load_system_prompt()
        return create_agent(
            model=self.llm, 
            middleware=[self.retry_middleware],
            tools=[search_steps],
            system_prompt=base_prompt,
            checkpointer=self.memory
        )

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
        return prompt_path.read_text()