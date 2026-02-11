"""Shared constants for baseline tools."""

from pathlib import Path

DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_RAG_TOP_K = 8
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_PHOENIX_SERVICE_NAME = "baseline-rag-agent"
DEFAULT_PHOENIX_ENDPOINT = "http://127.0.0.1:6006/v1/traces"
DEFAULT_STEPS_FILE = Path(__file__).parents[1] / "steps.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parents[1] / "features"

