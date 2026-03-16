"""Index few-shot descriptions (hooks) into a PGVector collection.

Reads few_shots_index.json, embeds the ``hook`` field of each entry,
and stores the vectors in PGVector with metadata (few_shot_id, file).

Processes entries in batches to handle thousands of few-shots efficiently.

Usage:
    python -m src.scripts.index_few_shots
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import sys
from pathlib import Path

from langchain_core.documents import Document

from src.configs import global_config
from src.utils.embeddings import get_vector_store

logger = logging.getLogger(__name__)


def _load_index(index_path: Path) -> list[dict]:
    """Load and validate the few-shots index JSON."""
    with open(index_path, encoding="utf-8") as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        raise ValueError("few_shots_index.json must be a JSON array")

    valid: list[dict] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            logger.warning("Entry %d is not a dict, skipping", i)
            continue
        missing = [k for k in ("id", "hook", "file") if k not in entry]
        if missing:
            logger.warning("Entry %d missing keys %s, skipping", i, missing)
            continue
        valid.append(entry)

    return valid


def _entries_to_documents(entries: list[dict]) -> list[Document]:
    """Convert index entries to langchain Documents for embedding."""
    docs: list[Document] = []
    for entry in entries:
        doc = Document(
            page_content=entry["hook"],
            metadata={
                "few_shot_id": entry["id"],
                "file": entry["file"],
            },
        )
        docs.append(doc)
    return docs


async def _index(index_path: Path) -> None:
    cfg = global_config.rag.few_shots
    entries = _load_index(index_path)

    if not entries:
        logger.warning("No valid entries found in %s", index_path)
        return

    logger.info("Loaded %d entries from %s", len(entries), index_path)

    documents = _entries_to_documents(entries)

    store = await get_vector_store(cfg.collection_name)

    logger.info("Clearing existing collection '%s'…", cfg.collection_name)
    await store.adelete_collection()
    store._async_init = False
    await store.__apost_init__()

    batch_size: int = cfg.get("batch_size", 100)
    total_batches = math.ceil(len(documents) / batch_size)

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(documents))
        batch = documents[start:end]

        await store.aadd_documents(batch)
        logger.info(
            "Indexed batch %d/%d (%d/%d items)",
            batch_idx + 1, total_batches, end, len(documents),
        )

    logger.info(
        "Indexed %d entries into collection '%s'",
        len(documents), cfg.collection_name,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    project_root = Path(__file__).resolve().parents[2]
    cfg = global_config.rag.few_shots
    index_path = project_root / cfg.index_path

    if not index_path.is_file():
        logger.error("Index file not found: %s", index_path)
        sys.exit(1)

    asyncio.run(_index(index_path))
    logger.info("Done.")


if __name__ == "__main__":
    main()
