"""Data models for expert metric evaluations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "1.0"

SEMANTIC_WEIGHTS = {
    "preconditions": 0.20,
    "actions": 0.30,
    "checks": 0.30,
    "step_order": 0.10,
    "scenario_completeness": 0.10,
}


def now_iso() -> str:
    """Return UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SemanticChecklist:
    preconditions: float
    actions: float
    checks: float
    step_order: float
    scenario_completeness: float
    comment: str = ""

    @property
    def weighted_score(self) -> float:
        return round(
            self.preconditions * SEMANTIC_WEIGHTS["preconditions"]
            + self.actions * SEMANTIC_WEIGHTS["actions"]
            + self.checks * SEMANTIC_WEIGHTS["checks"]
            + self.step_order * SEMANTIC_WEIGHTS["step_order"]
            + self.scenario_completeness * SEMANTIC_WEIGHTS["scenario_completeness"],
            4,
        )

    @property
    def is_semantically_correct(self) -> bool:
        return self.weighted_score >= 0.8

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["weights"] = SEMANTIC_WEIGHTS
        payload["weighted_score"] = self.weighted_score
        payload["is_semantically_correct"] = self.is_semantically_correct
        return payload


@dataclass
class StepMatchingChecklist:
    total_generated_steps: int
    matched_steps: int
    wrong_step_count: int = 0
    close_step_count: int = 0
    missing_step_definition_count: int = 0
    dropped_source_step_count: int = 0
    comment: str = ""

    @property
    def precision(self) -> float:
        if self.total_generated_steps <= 0:
            return 0.0
        value = self.matched_steps / self.total_generated_steps
        return round(max(0.0, min(1.0, value)), 4)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["precision"] = self.precision
        return payload


@dataclass
class CoverageChecklist:
    total_source_steps: int
    covered_steps: int
    no_matching_step_reason_count: int = 0
    parse_error_reason_count: int = 0
    merged_steps_reason_count: int = 0
    redundant_step_reason_count: int = 0
    comment: str = ""

    @property
    def completeness(self) -> float:
        if self.total_source_steps <= 0:
            return 0.0
        value = self.covered_steps / self.total_source_steps
        return round(max(0.0, min(1.0, value)), 4)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["completeness"] = self.completeness
        return payload


@dataclass
class CandidateInfo:
    source: str  # golden | generated_preset | generated_live
    feature_path: str
    is_golden_candidate: bool = False
    generation_model: str | None = None
    generation_provider: str | None = None
    generation_error: str | None = None


@dataclass
class EvaluationRecord:
    session_id: str
    expert: str
    test_id: str
    manual_test_path: str
    golden_feature_path: str | None
    candidate: CandidateInfo
    semantic_accuracy: SemanticChecklist
    step_matching_precision: StepMatchingChecklist
    coverage_completeness: CoverageChecklist
    overall_comment: str = ""
    saved_at: str = field(default_factory=now_iso)
    record_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "session_id": self.session_id,
            "expert": self.expert,
            "saved_at": self.saved_at,
            "test_id": self.test_id,
            "manual_test_path": self.manual_test_path,
            "golden_feature_path": self.golden_feature_path,
            "candidate": asdict(self.candidate),
            "semantic_accuracy": self.semantic_accuracy.to_dict(),
            "step_matching_precision": self.step_matching_precision.to_dict(),
            "coverage_completeness": self.coverage_completeness.to_dict(),
            "overall_comment": self.overall_comment,
        }


@dataclass
class SessionMetadata:
    session_id: str
    expert: str
    created_at: str
    updated_at: str
    schema_version: str
    manual_tests_dir: str
    golden_features_dir: str
    preset_features_dir: str | None
    results_dir: str
    evaluated_tests: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

