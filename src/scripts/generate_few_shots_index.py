"""Generate few_shots_index.json by sending each .feature file to an LLM.

The LLM produces a short Russian-language hook (description) optimised for
embedding-based similarity search.  The script writes a JSON array to
``src/configs/few_shots_index.json``.

Usage::

    python -m src.scripts.generate_few_shots_index           # full (re)generation
    python -m src.scripts.generate_few_shots_index --merge   # add only new files
    python -m src.scripts.generate_few_shots_index --dry-run # preview, don't write
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import build_chat_model
from src.configs import global_config

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "few_shot_hook_prompt.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _discover_features(few_shots_dir: Path) -> list[Path]:
    """Recursively find all .feature files under *few_shots_dir*."""
    return sorted(few_shots_dir.rglob("*.feature"))


def _load_existing_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.is_file():
        return []
    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        logger.warning("Existing index is not a list, ignoring")
        return []
    return data


def _load_prompt_template() -> str:
    if not _PROMPT_PATH.exists():
        logger.error("Prompt file not found: %s", _PROMPT_PATH)
        sys.exit(1)
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _get_llm():
    """Build the LLM from agent config (supports GigaChat mTLS)."""
    agent_config_path = Path(__file__).parent.parent / "agents" / "config.yml"
    if agent_config_path.exists():
        from omegaconf import OmegaConf
        agent_config = OmegaConf.load(agent_config_path)
        llm_params = dict(agent_config.get("llm_params", {}))
    else:
        llm_params = {"model": "gpt-4.1-mini", "temperature": 0.1}

    llm_params.setdefault("temperature", 0.1)
    return build_chat_model(llm_params)


def _clean_hook(hook: str) -> str:
    """Strip wrapping quotes the LLM might add."""
    hook = hook.strip()
    if (hook.startswith('"') and hook.endswith('"')) or \
       (hook.startswith("«") and hook.endswith("»")):
        hook = hook[1:-1].strip()
    return hook


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

async def _generate(
    few_shots_dir: Path,
    index_path: Path,
    *,
    merge: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Generate hooks for all .feature files and return the index."""
    files = _discover_features(few_shots_dir)
    if not files:
        logger.warning("No .feature files found in %s", few_shots_dir)
        return []

    logger.info("Found %d .feature file(s) in %s", len(files), few_shots_dir)

    file_rels = [str(f.relative_to(few_shots_dir)) for f in files]

    # Load existing index for --merge mode
    existing: list[dict[str, Any]] = []
    existing_files: set[str] = set()
    next_id = 1

    if merge:
        existing = _load_existing_index(index_path)
        existing_files = {e["file"] for e in existing if "file" in e}
        if existing:
            max_id = max(
                (e["id"] for e in existing if isinstance(e.get("id"), int)),
                default=0,
            )
            next_id = max_id + 1
        logger.info(
            "Merge mode: %d existing entries, %d files already indexed",
            len(existing), len(existing_files),
        )

    # Filter out already indexed files in merge mode
    to_process: list[tuple[Path, str]] = [
        (fpath, frel)
        for fpath, frel in zip(files, file_rels)
        if not (merge and frel in existing_files)
    ]

    if not to_process:
        logger.info("Nothing new to generate (all files already indexed)")
        return existing

    logger.info("%d file(s) to process", len(to_process))

    if dry_run:
        logger.info("Dry-run mode — files that would be processed:")
        for _, frel in to_process:
            logger.info("  %s", frel)
        return existing

    # Prepare LLM & prompt
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(_load_prompt_template())
    chain = prompt | llm

    # Sequential processing
    new_entries: list[dict[str, Any]] = []
    for i, (fpath, frel) in enumerate(to_process, 1):
        logger.info("[%d/%d] %s …", i, len(to_process), frel)
        content = fpath.read_text(encoding="utf-8")
        try:
            response = await chain.ainvoke({"feature_content": content})
            hook = _clean_hook(response.content)
        except Exception as exc:
            logger.error("  FAILED: %s", exc)
            continue

        new_entries.append({"id": next_id, "hook": hook, "file": frel})
        next_id += 1
        logger.info("  OK (%d chars)", len(hook))

    logger.info("Generated %d new hook(s)", len(new_entries))
    return existing + new_entries


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Генерация few_shots_index.json через LLM.",
    )
    p.add_argument(
        "--merge", action="store_true",
        help="Не пересоздавать хуки для уже проиндексированных файлов.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Только показать файлы для обработки, не вызывать LLM и не писать файл.",
    )
    p.add_argument(
        "--few-shots-dir", default=None,
        help="Путь к директории с .feature файлами (по умолчанию из конфига).",
    )
    p.add_argument(
        "--output", default=None,
        help="Путь к выходному JSON-файлу (по умолчанию из конфига).",
    )
    return p.parse_args()


async def _main() -> None:
    args = _parse_args()

    cfg = global_config.rag.few_shots
    few_shots_dir = Path(args.few_shots_dir) if args.few_shots_dir else _PROJECT_ROOT / cfg.few_shots_dir
    index_path = Path(args.output) if args.output else _PROJECT_ROOT / cfg.index_path

    if not few_shots_dir.is_dir():
        logger.error("Few-shots directory not found: %s", few_shots_dir)
        sys.exit(1)

    result = await _generate(
        few_shots_dir, index_path,
        merge=args.merge, dry_run=args.dry_run,
    )

    if args.dry_run:
        return

    if not result:
        logger.warning("Empty result — index file not written.")
        return

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d entries to %s", len(result), index_path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(_main())
    logger.info("Done.")


if __name__ == "__main__":
    main()
