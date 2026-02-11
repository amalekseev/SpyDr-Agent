"""Filesystem helpers for baseline pipelines."""

import json
from pathlib import Path


def ensure_existing_directory(directory: str) -> Path:
    """Validate and return a directory path."""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Директория не найдена: {directory}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {directory}")
    return dir_path


def list_text_files(directory: str) -> list[Path]:
    """Return sorted .txt files from a directory."""
    dir_path = ensure_existing_directory(directory)
    return sorted(dir_path.glob("*.txt"))


def read_text_with_fallback(file_path: Path) -> str:
    """Read text file in UTF-8 with CP1251 fallback."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="cp1251")


def write_text_with_trailing_newline(content: str, output_path: Path) -> None:
    """Write text and ensure single trailing newline."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = content if content.endswith("\n") else f"{content}\n"
    output_path.write_text(text, encoding="utf-8")


def save_json(data: dict, output_path: str) -> None:
    """Save JSON with UTF-8 and pretty formatting."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

