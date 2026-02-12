"""Typed models for baseline conversion and parser outputs."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FileProcessResult:
    """Result of converting a single source test file."""

    source_file: str
    status: str = "pending"
    output_file: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    """Aggregate conversion result for all input files."""

    input_directory: str
    output_directory: str
    steps_file: str
    model: str
    llm_provider: str = "openai"
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    files: list[dict[str, Any]] = field(default_factory=list)
    rag_tool_calls: int = 0
    rag_unresolved_steps: int = 0
    rag_validation_errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

