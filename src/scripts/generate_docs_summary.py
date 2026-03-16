"""Generate documentation artifacts for the agent system.

Usage:
    python -m src.scripts.generate_docs_summary            # generate both files
    python -m src.scripts.generate_docs_summary --hooks     # only docs_hooks.md
    python -m src.scripts.generate_docs_summary --summary   # only docs_summary.md

Outputs (saved to src/agents/prompts/):
    docs_hooks.md   — RAG retrieval hooks (terms, search cues, patterns)
    docs_summary.md — dense documentation summary
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from src.configs import global_config

logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = SCRIPTS_DIR / "prompts"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "agents" / "prompts"

LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}

TARGETS = {
    "hooks": {
        "prompt_file": PROMPTS_DIR / "hooks_prompt.md",
        "output_file": OUTPUT_DIR / "docs_hooks.md",
        "label": "RAG hooks",
    },
    "summary": {
        "prompt_file": PROMPTS_DIR / "summary_prompt.md",
        "output_file": OUTPUT_DIR / "docs_summary.md",
        "label": "documentation summary",
    },
}


def _discover_files(docs_dir: Path) -> list[Path]:
    files: list[Path] = []
    for ext in LOADERS:
        files.extend(docs_dir.glob(f"*{ext}"))
    return sorted(files)


def _load_documents(files: list[Path]) -> list:
    all_docs = []
    for fpath in files:
        loader_cls = LOADERS.get(fpath.suffix.lower())
        if not loader_cls:
            logger.warning("Skipping unsupported file: %s", fpath.name)
            continue

        try:
            loader = loader_cls(str(fpath))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = fpath.name
            all_docs.extend(docs)
            logger.info("  Loaded %s (%d page(s)/chunk(s))", fpath.name, len(docs))
        except Exception as e:
            logger.error("  Failed to load %s: %s", fpath.name, e)

    return all_docs


def _prepare_document_text(docs: list, max_chars: int = 15000) -> str:
    texts = []
    current_length = 0

    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        content = f"\n---\nSource: {source}\n\n{doc.page_content}"

        if current_length + len(content) > max_chars:
            remaining = max_chars - current_length
            if remaining > 100:
                texts.append(content[:remaining])
            texts.append("\n\n[Documents truncated due to length limits...]")
            break

        texts.append(content)
        current_length += len(content)

    return "".join(texts)


def _load_prompt_template(prompt_path: Path) -> str:
    if not prompt_path.exists():
        logger.error("Prompt file not found: %s", prompt_path)
        sys.exit(1)
    return prompt_path.read_text(encoding="utf-8")


async def _generate_text(docs: list, prompt_template: str, llm) -> str:
    document_text = _prepare_document_text(docs)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    response = await chain.ainvoke({"documents": document_text})
    return response.content


def _get_llm():
    agent_config_path = Path(__file__).parent.parent / "agents" / "config.yml"
    if agent_config_path.exists():
        from omegaconf import OmegaConf
        agent_config = OmegaConf.load(agent_config_path)
        llm_params = agent_config.get("llm_params", {})
    else:
        llm_params = {"model": "gpt-4.1-mini", "temperature": 0.1}

    return init_chat_model(**llm_params)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate documentation artifacts (RAG hooks and/or summary).",
    )
    parser.add_argument(
        "--hooks",
        action="store_true",
        help="Generate only docs_hooks.md (RAG retrieval hooks)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate only docs_summary.md (dense documentation summary)",
    )
    return parser.parse_args()


def _resolve_targets(args: argparse.Namespace) -> list[str]:
    if not args.hooks and not args.summary:
        return list(TARGETS.keys())
    targets = []
    if args.hooks:
        targets.append("hooks")
    if args.summary:
        targets.append("summary")
    return targets


async def _main() -> None:
    args = _parse_args()
    targets = _resolve_targets(args)

    project_root = Path(__file__).resolve().parents[2]
    docs_dir = project_root / global_config.rag.docs.path

    if not docs_dir.is_dir():
        logger.error("Documents directory not found: %s", docs_dir)
        sys.exit(1)

    files = _discover_files(docs_dir)
    if not files:
        logger.warning("No documents found in %s", docs_dir)
        for target_name in targets:
            cfg = TARGETS[target_name]
            cfg["output_file"].parent.mkdir(parents=True, exist_ok=True)
            placeholder = (
                f"# {cfg['label'].title()}\n\n"
                "No documents found in the docs/ directory.\n\n"
                "Please add documentation files (.pdf, .docx, .txt, .md) to generate content."
            )
            cfg["output_file"].write_text(placeholder, encoding="utf-8")
            logger.info("Wrote placeholder to %s", cfg["output_file"])
        return

    logger.info("Found %d document(s) in %s", len(files), docs_dir)

    docs = _load_documents(files)
    if not docs:
        logger.error("No documents could be loaded")
        sys.exit(1)

    logger.info("Total loaded: %d document chunk(s)", len(docs))

    logger.info("Initializing LLM...")
    llm = _get_llm()

    for target_name in targets:
        cfg = TARGETS[target_name]
        logger.info("Generating %s...", cfg["label"])

        prompt_template = _load_prompt_template(cfg["prompt_file"])
        result = await _generate_text(docs, prompt_template, llm)

        cfg["output_file"].parent.mkdir(parents=True, exist_ok=True)
        cfg["output_file"].write_text(result, encoding="utf-8")
        logger.info("Saved %s to %s (%d chars)", cfg["label"], cfg["output_file"], len(result))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(_main())
    logger.info("Done.")


if __name__ == "__main__":
    main()
