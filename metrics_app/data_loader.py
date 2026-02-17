"""Helpers for loading manual tests and feature files."""

from __future__ import annotations

from pathlib import Path


def resolve_path(raw_path: str, repo_root: Path) -> Path:
    """Resolve provided path against repo root if it is relative."""
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def list_manual_tests(manual_tests_dir: Path) -> list[Path]:
    """Return sorted list of .txt tests."""
    if not manual_tests_dir.exists():
        return []
    return sorted([path for path in manual_tests_dir.glob("*.txt") if path.is_file()])


def map_feature_files_by_stem(features_dir: Path) -> dict[str, Path]:
    """Map feature files by stem name."""
    if not features_dir.exists():
        return {}
    return {path.stem: path for path in sorted(features_dir.glob("*.feature")) if path.is_file()}


def read_text(path: Path) -> str:
    """Read UTF-8 text from file."""
    return path.read_text(encoding="utf-8")

