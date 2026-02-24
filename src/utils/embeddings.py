import os
import asyncio

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from src.configs import global_config

if global_config.embeddings.provider == "openai":
    from langchain_openai import OpenAIEmbeddings
    embed_model = OpenAIEmbeddings(**global_config.embeddings.params)
elif global_config.embeddings.provider == "gigachat":
    from langchain_gigachat import GigaChatEmbeddings
    embed_model = GigaChatEmbeddings(**global_config.embeddings.params)
else:
    raise ValueError(f"Unsupported embedding provider: {global_config.embeddings.provider}")

_vector_stores: dict[str, PGVector] = {}
_lock = asyncio.Lock()

async def get_vector_store(collection_name: str) -> PGVector:
    if collection_name not in _vector_stores:
        async with _lock:
            if collection_name not in _vector_stores:  # double-check
                store = PGVector(
                    embeddings=embed_model,
                    collection_name=collection_name,
                    connection=os.getenv("CONNECTION_STRING"),
                    distance_strategy=DistanceStrategy.COSINE,
                    use_jsonb=True,
                    async_mode=True,
                    create_extension=False  # Расширение vector должно быть установлено в БД заранее
                )
                await store.__apost_init__()
                _vector_stores[collection_name] = store
    return _vector_stores[collection_name]