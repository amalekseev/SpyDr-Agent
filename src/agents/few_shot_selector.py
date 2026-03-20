"""Embedding-based few-shot selector.

Searches PGVector for few-shot descriptions (hooks) similar to the user query,
then lazily loads the content of the matched ``.feature`` files from disk.

Before searching, the raw user query is summarised by an LLM into a short
hook-style description so that the embedding comparison is apple-to-apple
(hook ↔ hook, not raw-request ↔ hook).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import build_chat_model
from src.configs import global_config
from src.utils.embeddings import get_vector_store

logger = logging.getLogger(__name__)

_QUERY_PROMPT_PATH = (
    Path(__file__).resolve().parent / "prompts" / "few_shot_query_prompt.md"
)


class FewShotSelector:
    """Selects relevant few-shot examples via cosine similarity over hooks."""

    def __init__(self, few_shots_dir: Path | str, llm_params: dict[str, Any] | None = None) -> None:
        self._few_shots_dir = Path(few_shots_dir)
        self._llm_params = llm_params or {}
        self._llm = None
        self._prompt = None

    # ------------------------------------------------------------------
    # Lazy init
    # ------------------------------------------------------------------

    def _get_llm(self):
        if self._llm is None:
            params = dict(self._llm_params) if self._llm_params else {"model": "gpt-4.1-mini", "temperature": 0}
            params.setdefault("temperature", 0)
            self._llm = build_chat_model(params)
        return self._llm

    def _get_prompt(self) -> ChatPromptTemplate:
        if self._prompt is None:
            if _QUERY_PROMPT_PATH.exists():
                text = _QUERY_PROMPT_PATH.read_text(encoding="utf-8")
            else:
                logger.warning("FewShotSelector: prompt file not found: %s, using fallback", _QUERY_PROMPT_PATH)
                text = (
                    "Перефразируй запрос пользователя в краткое описание (1-3 предложения) "
                    "для поиска похожих BDD-тестов. Верни только текст описания.\n\n"
                    "Запрос: {user_request}"
                )
            self._prompt = ChatPromptTemplate.from_template(text)
        return self._prompt

    # ------------------------------------------------------------------
    # Query summarisation
    # ------------------------------------------------------------------

    async def _summarise_query(self, raw_query: str) -> str:
        """Run the raw user query through the LLM to produce a hook-style summary."""
        llm = self._get_llm()
        prompt = self._get_prompt()
        chain = prompt | llm

        logger.info("FewShotSelector: summarising user query (%d chars) …", len(raw_query))
        response = await chain.ainvoke({"user_request": raw_query})
        summary = response.content.strip()
        logger.info("FewShotSelector: summary = %r", summary[:200])
        return summary

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def select(self, query: str, top_k: int | None = None) -> list[dict[str, str]]:
        """Return top-K few-shots most similar to *query*.

        1. Summarises the raw query into a hook-style description via LLM.
        2. Searches PGVector collection ``few_shots`` by the summary embedding.
        3. For each hit loads the ``.feature`` file content from disk.
        4. Skips entries whose file is missing (logs a warning).

        Returns:
            List of dicts ``{"id": ..., "file": ..., "content": ...}``.
        """
        cfg = global_config.rag.few_shots
        k = top_k if top_k and top_k > 0 else cfg.top_k

        # Step 1: summarise the query so embedding space matches hooks
        try:
            search_query = await self._summarise_query(query)
        except Exception as exc:
            logger.warning("FewShotSelector: summarisation failed (%s), falling back to raw query", exc)
            search_query = query

        logger.info("FewShotSelector: searching top_k=%d", k)

        store = await get_vector_store(cfg.collection_name)

        try:
            results = await store.asimilarity_search_with_score(search_query, k=k)
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
