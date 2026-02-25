import inspect
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from langgraph.graph.state import CompiledStateGraph
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
from omegaconf import OmegaConf



def _filter_supported_kwargs(cls: type, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Оставляет только kwargs, принимаемые конструктором *cls*.

    Для Pydantic-моделей (например GigaChat) проверяет model_fields,
    т.к. __init__ у них имеет сигнатуру (*args, **kwargs).
    """
    if hasattr(cls, "model_fields"):
        valid = set(cls.model_fields.keys())
        return {k: v for k, v in kwargs.items() if k in valid}
    try:
        sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return kwargs
    params = sig.parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return kwargs
    valid = set(params.keys()) - {"self"}
    return {k: v for k, v in kwargs.items() if k in valid}


def _build_gigachat_llm(model: str, temperature: float = 0, **extra: Any) -> BaseChatModel:
    """Создаёт GigaChat с mTLS-аутентификацией из переменных окружения."""
    try:
        from langchain_gigachat import GigaChat as ChatGigaChat
    except ImportError as exc:
        raise ImportError(
            "Для провайдера gigachat установите пакет: "
            "pip install langchain-gigachat-lc1"
        ) from exc

    kwargs: dict[str, Any] = {"model": model, "temperature": temperature, **extra}

    env_map = {
        "GIGACHAT_AUTH_URL": "auth_url",
        "GIGACHAT_BASE_URL": "base_url",
        "GIGACHAT_VERIFY_SSL_CERTS": "verify_ssl_certs",
        "GIGACHAT_CA_BUNDLE_FILE": "ca_bundle_file",
        "GIGACHAT_TIMEOUT": "timeout",
    }
    for env_name, arg_name in env_map.items():
        val = os.getenv(env_name, "").strip()
        if not val:
            continue
        if arg_name == "verify_ssl_certs":
            kwargs[arg_name] = val.lower() in {"1", "true", "yes", "on"}
        elif arg_name == "timeout":
            try:
                kwargs[arg_name] = float(val)
            except ValueError:
                continue
        else:
            kwargs[arg_name] = val

    # mTLS-сертификаты
    cert_file = (
        os.getenv("GIGACHAT_CERT_FILE")
        or os.getenv("GIGACHAT_CLIENT_CERT_FILE")
        or ""
    ).strip()
    key_file = (
        os.getenv("GIGACHAT_KEY_FILE")
        or os.getenv("GIGACHAT_CLIENT_KEY_FILE")
        or ""
    ).strip()
    key_password = (
        os.getenv("GIGACHAT_KEY_PASSWORD")
        or os.getenv("GIGACHAT_KEY_FILE_PASSWORD")
        or ""
    ).strip()

    if not cert_file or not key_file:
        raise ValueError(
            "Для GigaChat (mTLS) задайте GIGACHAT_CERT_FILE и GIGACHAT_KEY_FILE "
            "(или алиасы GIGACHAT_CLIENT_CERT_FILE / GIGACHAT_CLIENT_KEY_FILE)."
        )

    kwargs["cert_file"] = cert_file
    kwargs["key_file"] = key_file
    if key_password:
        kwargs["key_file_password"] = key_password

    kwargs = _filter_supported_kwargs(ChatGigaChat, kwargs)
    return ChatGigaChat(**kwargs)


def build_chat_model(params: dict[str, Any]) -> BaseChatModel:
    """Фабрика LLM: маршрутизирует по полю ``provider`` в конфиге.

    Для переключения достаточно одной строки в ``config.yml``::

        provider: gigachat   # или openai

    Args:
        params: Словарь из секции ``llm_params`` конфига.

    Returns:
        Инициализированная чат-модель.
    """
    params = dict(params)  # не мутируем оригинал
    provider = params.pop("provider", "openai").strip().lower()

    if provider == "gigachat":
        return _build_gigachat_llm(**params)

    # OpenAI и другие провайдеры, поддерживаемые init_chat_model
    return init_chat_model(**params)



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
        self._llm: BaseChatModel = build_chat_model(llm_params)
    
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
