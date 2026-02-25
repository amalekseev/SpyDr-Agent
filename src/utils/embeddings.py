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
            connection=os.getenv("CONNECTION_STRING"),
            distance_strategy=DistanceStrategy.COSINE,
            use_jsonb=True,
            async_mode=True,
            create_extension=False,
        )
        await store.__apost_init__()
        _vector_stores[collection_name] = (store, loop)

    return _vector_stores[collection_name][0]