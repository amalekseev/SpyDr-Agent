"""Embedding model and PGVector store management.

Supports OpenAI and GigaChat providers.  GigaChat connections use mTLS
certificates read from environment variables — the same set of env vars
used by the LLM layer (``GIGACHAT_CERT_FILE``, ``GIGACHAT_KEY_FILE``, etc.).
"""

from __future__ import annotations

import asyncio
import inspect
import os
from typing import Any

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from src.configs import global_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _filter_supported_kwargs(cls: type, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Keep only kwargs accepted by *cls* constructor / Pydantic fields."""
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


def _build_gigachat_embeddings(**config_params: Any) -> Any:
    """Create :class:`GigaChatEmbeddings` with mTLS certs from env vars.

    Environment variables (same as for the chat model):
        ``GIGACHAT_AUTH_URL``, ``GIGACHAT_BASE_URL``,
        ``GIGACHAT_VERIFY_SSL_CERTS``, ``GIGACHAT_CA_BUNDLE_FILE``,
        ``GIGACHAT_TIMEOUT``,
        ``GIGACHAT_CERT_FILE`` (or ``GIGACHAT_CLIENT_CERT_FILE``),
        ``GIGACHAT_KEY_FILE``  (or ``GIGACHAT_CLIENT_KEY_FILE``),
        ``GIGACHAT_KEY_PASSWORD`` (or ``GIGACHAT_KEY_FILE_PASSWORD``).
    """
    from langchain_gigachat import GigaChatEmbeddings

    kwargs: dict[str, Any] = dict(config_params)

    # --- scalar env vars ---
    env_map: dict[str, str] = {
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

    # --- mTLS certificates ---
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

    kwargs = _filter_supported_kwargs(GigaChatEmbeddings, kwargs)
    return GigaChatEmbeddings(**kwargs)


# ---------------------------------------------------------------------------
# Embedding model singleton
# ---------------------------------------------------------------------------


def _build_embed_model() -> Any:
    """Instantiate the embedding model based on ``rag.provider`` config."""
    provider = global_config.rag.provider
    params = dict(global_config.rag.get("params", {}))

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(**params)

    if provider == "gigachat":
        return _build_gigachat_embeddings(**params)

    raise ValueError(f"Unsupported embedding provider: {provider}")


embed_model = _build_embed_model()

# ---------------------------------------------------------------------------
# PGVector store cache
# ---------------------------------------------------------------------------

_vector_stores: dict[str, tuple[PGVector, asyncio.AbstractEventLoop]] = {}
_bound_loop: asyncio.AbstractEventLoop | None = None
_lock: asyncio.Lock | None = None


def _ensure_async_driver(url: str) -> str:
    """Ensure the SQLAlchemy URL uses the async-capable ``psycopg`` (v3) driver.

    Plain ``postgresql://`` or ``postgresql+psycopg2://`` URLs are rewritten
    to ``postgresql+psycopg://`` so that :class:`PGVector` with
    ``async_mode=True`` works correctly.
    """
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _resolve_connection_string() -> str:
    """Return a database connection string from environment variables.

    Checks ``CONNECTION_STRING``, ``BASELINE_RAG_DB_URL``, and
    ``DATABASE_URL`` in order.  Raises :class:`ValueError` with a clear
    message when none of them are set.

    The returned URL is guaranteed to use the async-capable ``psycopg`` driver.
    """
    for var in ("CONNECTION_STRING", "BASELINE_RAG_DB_URL", "DATABASE_URL"):
        value = os.getenv(var, "").strip()
        if value:
            return _ensure_async_driver(value)
    raise ValueError(
        "URL базы данных не задан. Установите переменную окружения "
        "CONNECTION_STRING (или BASELINE_RAG_DB_URL / DATABASE_URL)."
    )


def _get_lock() -> asyncio.Lock:
    global _lock, _bound_loop
    loop = asyncio.get_running_loop()
    if _bound_loop is not loop:
        _lock = asyncio.Lock()
        _bound_loop = loop
    return _lock


async def get_vector_store(collection_name: str) -> PGVector:
    loop = asyncio.get_running_loop()
    lock = _get_lock()

    cached = _vector_stores.get(collection_name)
    if cached is not None and cached[1] is loop:
        return cached[0]

    async with lock:
        cached = _vector_stores.get(collection_name)
        if cached is not None and cached[1] is loop:
            return cached[0]

        store = PGVector(
            embeddings=embed_model,
            collection_name=collection_name,
            connection=_resolve_connection_string(),
            distance_strategy=DistanceStrategy.COSINE,
            use_jsonb=True,
            async_mode=True,
            create_extension=False,
        )
        await store.__apost_init__()
        _vector_stores[collection_name] = (store, loop)

    return _vector_stores[collection_name][0]