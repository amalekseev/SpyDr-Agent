import os
import asyncio

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from src.configs import global_config

if global_config.rag.provider == "openai":
    from langchain_openai import OpenAIEmbeddings
    embed_model = OpenAIEmbeddings(**global_config.rag.params)
elif global_config.rag.provider == "gigachat":
    from langchain_gigachat import GigaChatEmbeddings
    embed_model = GigaChatEmbeddings(**global_config.rag.params)
else:
    raise ValueError(f"Unsupported embedding provider: {global_config.rag.provider}")

_vector_stores: dict[str, PGVector] = {}
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