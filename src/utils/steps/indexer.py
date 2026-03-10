"""Async indexer: parse step source files and upsert into PGVector.

Usage from code::

    from src.utils.steps.indexer import reindex_steps
    stats = await reindex_steps()          # full reindex
    stats = await reindex_steps(force=False)  # skip if collection already has data

Usage from CLI::

    python -m src.scripts.index_steps          # full reindex
    python -m src.scripts.index_steps --check  # index only if empty
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document

from src.configs import global_config
from src.utils.embeddings import embed_model, get_vector_store

from .catalog import build_steps_index
from .parser import parse_steps_directory

logger = logging.getLogger(__name__)

# Hard limits for the text sent to the embedding API.
_MAX_EMBED_CHARS: int = 8_000
_MAX_DOCSTRING_CHARS: int = 500


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@dataclass
class IndexStats:
    """Result of a reindex operation."""

    parsed: int = 0
    indexed: int = 0
    skipped: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parsed": self.parsed,
            "indexed": self.indexed,
            "skipped": self.skipped,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Document building
# ---------------------------------------------------------------------------


def _build_embed_text(step: dict[str, Any]) -> str:
    """Build the text representation of a step for the embedding model."""
    placeholders = ", ".join(p["name"] for p in step.get("placeholders", []))
    step_type = step.get("type", "")
    if isinstance(step_type, list):
        type_str = ",".join(sorted(step_type))
    else:
        type_str = str(step_type)

    raw_doc = step.get("docstring") or ""
    if len(raw_doc) > _MAX_DOCSTRING_CHARS:
        raw_doc = raw_doc[:_MAX_DOCSTRING_CHARS] + "…"

    text = (
        f"type: {type_str}\n"
        f"pattern: {step.get('pattern', '')}\n"
        f"placeholders: {placeholders}\n"
        f"doc: {raw_doc}\n"
        f"source: {step.get('source_file') or ''}"
    )
    if len(text) > _MAX_EMBED_CHARS:
        logger.warning(
            "Embedding text truncated for step %s: %d → %d chars",
            step.get("step_id"),
            len(text),
            _MAX_EMBED_CHARS,
        )
        text = text[:_MAX_EMBED_CHARS]
    return text


def _step_to_document(step: dict[str, Any]) -> Document:
    """Convert a parsed step dict into a LangChain Document."""
    step_type = step.get("type", "")
    if isinstance(step_type, list):
        type_str = ",".join(sorted(step_type))
    else:
        type_str = str(step_type)

    metadata: dict[str, Any] = {
        "step_id": step["step_id"],
        "step_type": type_str,
        "pattern": step["pattern"],
        "placeholders": step.get("placeholders", []),
        "parser_kind": step.get("parser_kind", "parse"),
        "docstring": step.get("docstring") or "",
        "source_file": step.get("source_file") or "",
        "function_name": step.get("function_name") or "",
        "line_number": step.get("line_number"),
        "requires_docstring": bool(step.get("requires_docstring")),
        "requires_datatable": bool(step.get("requires_datatable")),
    }

    return Document(
        page_content=_build_embed_text(step),
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def reindex_steps(
    *,
    steps_dir: str | None = None,
    collection_name: str | None = None,
    force: bool = True,
    batch_size: int = 50,
) -> IndexStats:
    """Parse step source files and upsert them into PGVector.

    Args:
        steps_dir: Override for the step files directory.
                   Defaults to ``steps_dir`` from config.
        collection_name: Override for the PGVector collection name.
                         Defaults to ``rag.steps.collection_name``.
        force: If ``True`` (default), clear the collection and reindex
               from scratch.  If ``False``, skip when data already exists.
        batch_size: Number of documents to add per batch.

    Returns:
        :class:`IndexStats` with counts and any errors.
    """
    from src.utils.steps import _resolve_steps_dir  # avoid circular at module level

    stats = IndexStats()
    coll = collection_name or global_config.rag.steps.collection_name

    # 1. Parse step source files
    resolved_dir = str(_resolve_steps_dir()) if steps_dir is None else steps_dir
    logger.info("Parsing steps from %s …", resolved_dir)

    try:
        steps_data = parse_steps_directory(resolved_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        stats.errors.append(str(exc))
        logger.error("Failed to parse steps directory: %s", exc)
        return stats

    all_steps = steps_data.get("steps", [])
    stats.parsed = len(all_steps)
    logger.info("Parsed %d steps from %d files", stats.parsed, len(steps_data.get("files_parsed", [])))

    if not all_steps:
        logger.warning("No steps found — nothing to index.")
        return stats

    # 2. Refresh the in-memory singleton index
    from src.utils.steps import reload_steps
    reload_steps()
    logger.info("In-memory index reloaded")

    # 3. Get the vector store
    store = await get_vector_store(coll)

    # 4. Check whether we need to index
    if not force:
        try:
            existing = await store.asimilarity_search("test", k=1)
            if existing:
                logger.info(
                    "Collection '%s' already has data and force=False — skipping.",
                    coll,
                )
                stats.skipped = True
                return stats
        except Exception:
            pass  # collection might be empty or broken — proceed with indexing

    # 5. Clear existing data
    logger.info("Clearing collection '%s' …", coll)
    try:
        await store.adelete_collection()
        # Re-initialize the collection after clearing.
        store._async_init = False
        await store.__apost_init__()
    except Exception as exc:
        logger.warning("Could not clear collection (may be fresh): %s", exc)

    # 6. Build documents and upsert in batches
    docs: list[Document] = []
    ids: list[str] = []
    for step in all_steps:
        try:
            docs.append(_step_to_document(step))
            ids.append(step["step_id"])
        except Exception as exc:
            msg = f"Error building document for step {step.get('step_id')}: {exc}"
            logger.error(msg)
            stats.errors.append(msg)

    logger.info("Indexing %d documents into '%s' (batch_size=%d) …", len(docs), coll, batch_size)

    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        try:
            await store.aadd_documents(batch_docs, ids=batch_ids)
            stats.indexed += len(batch_docs)
            logger.info("  batch %d–%d indexed (%d/%d)", i, i + len(batch_docs), stats.indexed, len(docs))
        except Exception as exc:
            msg = f"Error indexing batch {i}–{i + len(batch_docs)}: {exc}"
            logger.error(msg)
            stats.errors.append(msg)

    logger.info(
        "Indexing complete: %d parsed, %d indexed, %d errors",
        stats.parsed,
        stats.indexed,
        len(stats.errors),
    )
    return stats
