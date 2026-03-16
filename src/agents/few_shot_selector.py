"""Embedding-based few-shot selector.

Searches PGVector for few-shot descriptions (hooks) similar to the user query,
then lazily loads the content of the matched ``.feature`` files from disk.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.configs import global_config
from src.utils.embeddings import get_vector_store

logger = logging.getLogger(__name__)


class FewShotSelector:
    """Selects relevant few-shot examples via cosine similarity over hooks."""

    def __init__(self, few_shots_dir: Path | str) -> None:
        self._few_shots_dir = Path(few_shots_dir)

    async def select(self, query: str, top_k: int | None = None) -> list[dict[str, str]]:
        """Return top-K few-shots most similar to *query*.

        1. Searches PGVector collection ``few_shots`` by the query embedding.
        2. For each hit loads the ``.feature`` file content from disk.
        3. Skips entries whose file is missing (logs a warning).

        Returns:
            List of dicts ``{"id": ..., "file": ..., "content": ...}``.
        """
        cfg = global_config.rag.few_shots
        k = top_k if top_k and top_k > 0 else cfg.top_k

        logger.info("FewShotSelector: query=%r, top_k=%d", query[:120], k)

        store = await get_vector_store(cfg.collection_name)

        try:
            results = await store.asimilarity_search_with_score(query, k=k)
        except Exception as exc:
            logger.error("FewShotSelector: search failed: %s", exc)
            return []

        selected: list[dict[str, str]] = []
        for doc, _score in results:
            meta: dict[str, Any] = doc.metadata or {}
            few_shot_id = meta.get("few_shot_id", "")
            file_rel = meta.get("file", "")

            if not file_rel:
                logger.warning("FewShotSelector: entry %r has no file, skipping", few_shot_id)
                continue

            file_path = self._few_shots_dir / file_rel
            if not file_path.is_file():
                logger.warning(
                    "FewShotSelector: file not found: %s (id=%s), skipping",
                    file_path, few_shot_id,
                )
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.warning(
                    "FewShotSelector: failed to read %s: %s, skipping",
                    file_path, exc,
                )
                continue

            selected.append({
                "id": few_shot_id,
                "file": file_rel,
                "content": content,
            })

        logger.info("FewShotSelector: selected %d few-shot(s)", len(selected))
        return selected
