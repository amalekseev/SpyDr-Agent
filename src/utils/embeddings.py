import os
import asyncio

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
from langchain_openai import OpenAIEmbeddings

from src.configs import global_config

embed_model = OpenAIEmbeddings(model=global_config.embeddings.embed_model)

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