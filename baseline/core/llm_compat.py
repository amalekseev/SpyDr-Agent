"""OpenAI-compatible client adapters for OpenAI and GigaChat backends."""

from __future__ import annotations

import inspect
import json
import os
import uuid
from types import SimpleNamespace
from typing import Any

from openai import OpenAI

SUPPORTED_LLM_PROVIDERS = {"openai", "gigachat"}


def normalize_llm_provider(value: str | None) -> str:
    """Normalize provider value and validate supported backends."""
    provider = (value or os.getenv("BASELINE_LLM_PROVIDER") or "openai").strip().lower()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(
            f"Неизвестный LLM provider: {provider}. Поддерживаются: {', '.join(sorted(SUPPORTED_LLM_PROVIDERS))}"
        )
    return provider


def build_openai_compatible_client(
    *,
    llm_provider: str | None = None,
    openai_api_key: str | None = None,
) -> Any:
    """Create client object with OpenAI-like `chat.completions` and `embeddings` API."""
    provider = normalize_llm_provider(llm_provider)
    if provider == "openai":
        return _build_openai_client(openai_api_key=openai_api_key)
    return _GigaChatOpenAICompatClient()


def _build_openai_client(*, openai_api_key: str | None = None) -> OpenAI:
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY не найден. Установите переменную окружения или задайте ключ в конфиге."
        )
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


class _GigaChatOpenAICompatClient:
    """Adapter that mimics small subset of OpenAI client API used by this project."""

    def __init__(self) -> None:
        self._chat_model_cls, self._embeddings_cls = _import_gigachat_classes()
        self._gigachat_common_kwargs = _build_gigachat_common_kwargs(self._chat_model_cls)
        self.chat = SimpleNamespace(completions=_GigaChatChatCompletions(self))
        self.embeddings = _GigaChatEmbeddings(self)

    def _create_chat_model(self, *, model: str, temperature: float) -> Any:
        kwargs = dict(self._gigachat_common_kwargs)
        kwargs.update({"model": model, "temperature": temperature})
        return self._chat_model_cls(**_filter_supported_kwargs(self._chat_model_cls, kwargs))

    def _create_embeddings_model(self, *, model: str) -> Any:
        kwargs = dict(self._gigachat_common_kwargs)
        kwargs.update({"model": model})
        return self._embeddings_cls(**_filter_supported_kwargs(self._embeddings_cls, kwargs))


class _GigaChatChatCompletions:
    def __init__(self, parent: _GigaChatOpenAICompatClient) -> None:
        self._parent = parent

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0,
        **_: Any,
    ) -> Any:
        del response_format  # JSON mode is enforced by prompts; keeps signature compatible.
        chat_model = self._parent._create_chat_model(model=model, temperature=temperature)
        runnable = chat_model
        if tools:
            bind_kwargs: dict[str, Any] = {}
            if tool_choice:
                bind_kwargs["tool_choice"] = tool_choice
            try:
                runnable = chat_model.bind_tools(tools, **bind_kwargs)
            except TypeError:
                runnable = chat_model.bind_tools(tools)

        lc_messages = _to_langchain_messages(messages)
        ai_message = runnable.invoke(lc_messages)
        return _to_openai_chat_response(ai_message)


class _GigaChatEmbeddings:
    def __init__(self, parent: _GigaChatOpenAICompatClient) -> None:
        self._parent = parent

    def create(self, *, model: str, input: str | list[str], **_: Any) -> Any:
        texts = [input] if isinstance(input, str) else input
        embeddings_model = self._parent._create_embeddings_model(model=model)
        vectors = [embeddings_model.embed_query(text) for text in texts]
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=vector) for vector in vectors]
        )


def _to_openai_chat_response(ai_message: Any) -> Any:
    content = _extract_text_content(getattr(ai_message, "content", ""))
    tool_calls = []
    for raw_call in getattr(ai_message, "tool_calls", []) or []:
        call_id = raw_call.get("id") or f"call_{uuid.uuid4().hex[:12]}"
        call_name = raw_call.get("name", "")
        call_args = raw_call.get("args", {})
        if isinstance(call_args, str):
            arguments = call_args
        else:
            arguments = json.dumps(call_args, ensure_ascii=False)
        tool_calls.append(
            SimpleNamespace(
                id=call_id,
                type="function",
                function=SimpleNamespace(name=call_name, arguments=arguments),
            )
        )
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)


def _to_langchain_messages(messages: list[dict[str, Any]]) -> list[Any]:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

    converted: list[Any] = []
    for message in messages:
        role = str(message.get("role", "")).lower()
        content = _extract_text_content(message.get("content", ""))
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            ai_tool_calls: list[dict[str, Any]] = []
            for call in message.get("tool_calls", []) or []:
                call_id = call.get("id") or f"call_{uuid.uuid4().hex[:12]}"
                function_block = call.get("function") or {}
                raw_arguments = function_block.get("arguments", "{}")
                if isinstance(raw_arguments, str):
                    try:
                        parsed_arguments = json.loads(raw_arguments)
                    except json.JSONDecodeError:
                        parsed_arguments = {}
                else:
                    parsed_arguments = raw_arguments
                ai_tool_calls.append(
                    {"id": call_id, "name": function_block.get("name", ""), "args": parsed_arguments}
                )
            if ai_tool_calls:
                converted.append(AIMessage(content=content, tool_calls=ai_tool_calls))
            else:
                converted.append(AIMessage(content=content))
        elif role == "tool":
            converted.append(
                ToolMessage(
                    content=content,
                    tool_call_id=str(message.get("tool_call_id", "")),
                )
            )
    return converted


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
            elif isinstance(item, str):
                chunks.append(item)
        return "\n".join(chunks).strip()
    return str(content or "")


def _import_gigachat_classes() -> tuple[type[Any], type[Any]]:
    try:
        from langchain_gigachat.chat_models import GigaChat as ChatModelClass
    except ImportError:
        from langchain_gigachat.chat_models import ChatGigaChat as ChatModelClass
    try:
        from langchain_gigachat.embeddings import GigaChatEmbeddings as EmbeddingsClass
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать GigaChatEmbeddings из langchain_gigachat."
        ) from exc
    return ChatModelClass, EmbeddingsClass


def _build_gigachat_common_kwargs(chat_model_cls: type[Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    env_to_arg = {
        "GIGACHAT_AUTH_URL": "auth_url",
        "GIGACHAT_BASE_URL": "base_url",
        "GIGACHAT_VERIFY_SSL_CERTS": "verify_ssl_certs",
        "GIGACHAT_CA_BUNDLE_FILE": "ca_bundle_file",
        "GIGACHAT_TIMEOUT": "timeout",
    }
    for env_name, arg_name in env_to_arg.items():
        raw_value = os.getenv(env_name)
        if raw_value is None or raw_value == "":
            continue
        if arg_name == "verify_ssl_certs":
            kwargs[arg_name] = raw_value.strip().lower() in {"1", "true", "yes", "on"}
        elif arg_name == "timeout":
            try:
                kwargs[arg_name] = float(raw_value)
            except ValueError:
                continue
        else:
            kwargs[arg_name] = raw_value

    cert_file = (os.getenv("GIGACHAT_CERT_FILE") or os.getenv("GIGACHAT_CLIENT_CERT_FILE") or "").strip()
    key_file = (os.getenv("GIGACHAT_KEY_FILE") or os.getenv("GIGACHAT_CLIENT_KEY_FILE") or "").strip()
    key_password = (
        os.getenv("GIGACHAT_KEY_PASSWORD") or os.getenv("GIGACHAT_KEY_FILE_PASSWORD") or ""
    ).strip()
    if not cert_file or not key_file:
        raise ValueError(
            "Для GigaChat (mTLS) задайте пути GIGACHAT_CERT_FILE/GIGACHAT_KEY_FILE "
            "(или алиасы GIGACHAT_CLIENT_CERT_FILE/GIGACHAT_CLIENT_KEY_FILE)."
        )

    cert_arg_names = ("cert_file", "client_cert_file", "ssl_cert_file", "cert_path")
    key_arg_names = ("key_file", "client_key_file", "ssl_key_file", "key_path")
    key_password_arg_names = (
        "key_file_password",
        "client_key_password",
        "ssl_key_password",
        "key_password",
    )
    for arg_name in cert_arg_names:
        kwargs[arg_name] = cert_file
    for arg_name in key_arg_names:
        kwargs[arg_name] = key_file
    if key_password:
        for arg_name in key_password_arg_names:
            kwargs[arg_name] = key_password

    # Fail fast with clear message if installed package does not expose cert-based args.
    try:
        signature = inspect.signature(chat_model_cls.__init__)
        init_params = set(signature.parameters.keys())
    except (TypeError, ValueError):
        init_params = set()
    if init_params and not any(name in init_params for name in cert_arg_names):
        raise ValueError(
            "Текущая версия langchain_gigachat не поддерживает передачу client cert через параметры модели."
        )
    if init_params and not any(name in init_params for name in key_arg_names):
        raise ValueError(
            "Текущая версия langchain_gigachat не поддерживает передачу client key через параметры модели."
        )

    return _filter_supported_kwargs(chat_model_cls, kwargs)


def _filter_supported_kwargs(target_cls: type[Any], kwargs: dict[str, Any]) -> dict[str, Any]:
    try:
        signature = inspect.signature(target_cls.__init__)
    except (TypeError, ValueError):
        return kwargs
    valid_names = set(signature.parameters.keys())
    valid_names.discard("self")
    return {name: value for name, value in kwargs.items() if name in valid_names}
