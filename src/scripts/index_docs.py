"""Index documents from the docs/ directory into a PGVector collection.

Usage:
    python -m src.scripts.index_docs
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.configs import global_config
from src.utils.embeddings import get_vector_store

logger = logging.getLogger(__name__)

LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}


def _discover_files(docs_dir: Path) -> list[Path]:
    files: list[Path] = []
    for ext in LOADERS:
        files.extend(docs_dir.glob(f"*{ext}"))
    return sorted(files)


async def _index(docs_dir: Path) -> None:
    cfg = global_config.rag.docs
    files = _discover_files(docs_dir)

    if not files:
        logger.warning("No documents found in %s", docs_dir)
        return

    logger.info("Found %d document(s) in %s", len(files), docs_dir)

    all_docs = []
    for fpath in files:
        loader_cls = LOADERS[fpath.suffix.lower()]
        loader = loader_cls(str(fpath))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = fpath.name
        all_docs.extend(docs)
        logger.info("  Loaded %s (%d page(s))", fpath.name, len(docs))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
    )
    chunks = splitter.split_documents(all_docs)
    logger.info("Split into %d chunk(s)", len(chunks))

    store = await get_vector_store(cfg.collection_name)

    logger.info("Clearing existing collection '%s'…", cfg.collection_name)
    await store.adelete_collection()
    store._async_init = False
    await store.__apost_init__()

    await store.aadd_documents(chunks)
    logger.info(
        "Indexed %d chunk(s) from %d file(s) into collection '%s'",
        len(chunks), len(files), cfg.collection_name,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    project_root = Path(__file__).resolve().parents[2]
    docs_dir = project_root / global_config.rag.docs.path

    if not docs_dir.is_dir():
        logger.error("Documents directory not found: %s", docs_dir)
        sys.exit(1)

    asyncio.run(_index(docs_dir))
    logger.info("Done.")


if __name__ == "__main__":
    main()
