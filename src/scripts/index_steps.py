"""Index BDD step definitions into the PGVector collection.

Usage::

    python -m src.scripts.index_steps                       # reindex default steps
    python -m src.scripts.index_steps --check               # skip if collection has data
    python -m src.scripts.index_steps --project my_project  # custom steps for one project
    python -m src.scripts.index_steps --all-projects        # custom steps for all projects
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from src.configs import global_config
from src.utils.steps.indexer import IndexStats, reindex_steps

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Индексация BDD шагов в PGVector.")
    p.add_argument("--check", action="store_true", help="Не переиндексировать, если данные есть.")
    p.add_argument("--steps-dir", default=None, help="Путь к директории со step-файлами.")
    p.add_argument("--collection", default=None, help="Имя коллекции PGVector.")
    p.add_argument("--batch-size", type=int, default=50, help="Размер батча.")

    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--project", default=None, help="Кастомные шаги для одного проекта.")
    grp.add_argument("--all-projects", action="store_true", help="Кастомные шаги для всех проектов.")
    return p


def _print_stats(stats: IndexStats, label: str = "") -> None:
    pfx = f"[{label}] " if label else ""
    if stats.skipped:
        print(f"{pfx}Коллекция уже содержит данные — пропущено (--check).")
        return
    print(f"{pfx}Распаршено: {stats.parsed}  Загружено: {stats.indexed}")
    for err in stats.errors:
        print(f"  {pfx}ERROR: {err}")


async def _reindex_project(project_id: str, *, force: bool, batch_size: int) -> IndexStats:
    from src.utils.steps import _resolve_custom_steps_dir, get_custom_collection_name, get_steps_index

    custom_dir = _resolve_custom_steps_dir(project_id)
    if custom_dir is None or not custom_dir.is_dir():
        stats = IndexStats()
        stats.errors.append(f"Проект '{project_id}' не сконфигурирован или директория не найдена.")
        return stats

    # Custom step IDs continue numbering after default steps
    start_id = len(get_steps_index()) + 1

    return await reindex_steps(
        steps_dir=str(custom_dir),
        collection_name=get_custom_collection_name(project_id),
        start_id=start_id,
        force=force,
        batch_size=batch_size,
    )


async def _run(args: argparse.Namespace) -> int:
    force = not args.check

    if args.project:
        stats = await _reindex_project(args.project, force=force, batch_size=args.batch_size)
        _print_stats(stats, label=args.project)
        return 1 if stats.errors else 0

    if args.all_projects:
        projects = dict(global_config.get("projects") or {})
        if not projects:
            print("В конфиге нет проектов.")
            return 0
        has_errors = False
        for pid in projects:
            stats = await _reindex_project(pid, force=force, batch_size=args.batch_size)
            _print_stats(stats, label=pid)
            if stats.errors:
                has_errors = True
        return 1 if has_errors else 0

    stats = await reindex_steps(
        steps_dir=args.steps_dir,
        collection_name=args.collection,
        force=force,
        batch_size=args.batch_size,
    )
    _print_stats(stats)
    return 1 if stats.errors else 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    args = _build_parser().parse_args()
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
