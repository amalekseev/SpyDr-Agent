import json
import logging
from typing import Optional

from langchain.tools import tool, ToolRuntime

from src.agents import config
from src.utils.streaming import set_status
from src.utils.embeddings import get_vector_store, embed_model
from src.configs import global_config

logger = logging.getLogger(__name__)


@tool
async def search_steps(
    runtime: ToolRuntime,
    query: str,
    top_k: Optional[int] = None
) -> str:
    """Семантический поиск BDD шагов в векторной базе. Возвращает кандидаты с step_id.

    Args:
        query: Естественноязыковое описание нужного шага (на русском).
        top_k: Количество результатов (по умолчанию берётся из конфига).

    Returns:
        JSON-строка со списком найденных шагов.
    """
    k = top_k if top_k and top_k > 0 else global_config.embeddings.top_k

    logger.info("search_steps: query=%r, top_k=%d", query, k)
    set_status(f"Ищу шаги: «{query[:60]}»")

    try:
        query_embedding = (await embed_model.aembed_documents([query]))[0]
    except Exception as e:
        error_msg = f"Ошибка при векторизации запроса: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    vector_store = await get_vector_store(global_config.embeddings.collection_name)
    try:
        docs_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
            embedding=query_embedding,
            k=k
        )
    except Exception as e:
        error_msg = f"Ошибка при поиске в коллекции {global_config.embeddings.collection_name}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    results = []
    for doc, distance in docs_with_scores:
        meta = doc.metadata or {}
        results.append({
            "id": meta.get("step_id", ""),
            "type": meta.get("step_type", ""),
            "pattern": meta.get("pattern", ""),
            "placeholders": meta.get("placeholders", []),
            "docstring": meta.get("docstring"),
            "source_file": meta.get("source_file"),
            "function_name": meta.get("function_name")
        })

    set_status(f"Найдено {len(results)} шагов")
    logger.info("search_steps: найдено %d результатов", len(results))

    return json.dumps({"steps": results}, ensure_ascii=False)
