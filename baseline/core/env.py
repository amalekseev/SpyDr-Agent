"""Environment bootstrap helpers for baseline package."""

from __future__ import annotations

from dotenv import load_dotenv

_DOTENV_LOADED = False


def load_project_env() -> None:
    """Load .env once per process so os.getenv calls see project settings."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    load_dotenv()
    _DOTENV_LOADED = True
