from abc import ABC, abstractmethod
from typing import Any, Optional

from langgraph.graph.state import CompiledStateGraph
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
from omegaconf import OmegaConf


class BaseAgent(ABC):
    """Базовая реализация агента"""
    
    def __init__(self, config: OmegaConf) -> None:
        """Инициализирует базовые зависимости агента.

        Args:
            config: Конфигурация агента с параметрами LLM и запуска.

        Returns:
            None.
        """
        self._config = config
        self._graph: Optional[CompiledStateGraph] = None
        llm_params: dict[str, Any] = config.get("llm_params", {})
        self._llm: BaseChatModel = init_chat_model(**llm_params)
    
    @property
    def config(self) -> OmegaConf:
        """Возвращает конфигурацию агента.

        Args:
            None.

        Returns:
            Конфигурация агента.
        """
        return self._config
    
    @property
    def llm(self) -> BaseChatModel:
        """Возвращает инициализированную языковую модель.

        Args:
            None.

        Returns:
            Экземпляр чат-модели.
        """
        return self._llm
    
    @property
    def graph(self) -> CompiledStateGraph:
        """Возвращает граф агента, создавая его при первом обращении.

        Args:
            None.

        Returns:
            Скомпилированный граф агента.
        """
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph
    
    @abstractmethod
    def _build_graph(self) -> CompiledStateGraph:
        """Строит и возвращает граф агента.

        Args:
            None.

        Returns:
            Скомпилированный граф агента.
        """
        ...