"""Index BDD step definitions into the PGVector collection.

Parses step source files, builds embeddings, and upserts them into the
vector store used by the interactive agent's ``search_steps`` tool.

Usage::

    python -m src.scripts.index_steps             # full reindex (default)
    python -m src.scripts.index_steps --check      # index only if collection is empty
    python -m src.scripts.index_steps --batch-size 100
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from src.utils.steps.indexer import reindex_steps

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Индексация BDD шагов в PGVector для семантического поиска агентом.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Не переиндексировать, если коллекция уже содержит данные.",
    )
    parser.add_argument(
        "--steps-dir",
        default=None,
        help="Путь к директории со step-файлами (по умолчанию из конфига).",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Имя коллекции PGVector (по умолчанию из конфига).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Размер батча при загрузке в PGVector (по умолчанию 50).",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    stats = await reindex_steps(
        steps_dir=args.steps_dir,
        collection_name=args.collection,
        force=not args.check,
        batch_size=args.batch_size,
    )

    if stats.skipped:
        print("Коллекция уже содержит данные — переиндексация пропущена (--check).")
        return 0

    print(f"\nРезультат индексации:")
    print(f"  Распаршено шагов:   {stats.parsed}")
    print(f"  Загружено в PGVector: {stats.indexed}")

    if stats.errors:
        print(f"  Ошибки ({len(stats.errors)}):")
        for err in stats.errors:
            print(f"    - {err}")
        return 1

    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = _build_parser()
    args = parser.parse_args()

    exit_code = asyncio.run(_run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
