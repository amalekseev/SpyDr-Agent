"""Persistence helpers for metrics app session files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import SCHEMA_VERSION, SessionMetadata, now_iso


def sanitize_session_id(raw_value: str) -> str:
    """Keep session id filesystem-safe and human-readable."""
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw_value.strip())
    return cleaned or "session"


def ensure_session_dir(results_dir: Path, session_id: str) -> Path:
    """Create the session directory if needed and return its path."""
    session_dir = results_dir / sanitize_session_id(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def metadata_path(session_dir: Path) -> Path:
    return session_dir / "metadata.json"


def evaluations_path(session_dir: Path) -> Path:
    return session_dir / "evaluations.jsonl"


def summary_path(session_dir: Path) -> Path:
    return session_dir / "summary.csv"


def load_or_create_metadata(
    *,
    session_dir: Path,
    session_id: str,
    expert: str,
    manual_tests_dir: Path,
    golden_features_dir: Path,
    preset_features_dir: Path | None,
    results_dir: Path,
) -> dict[str, Any]:
    """Load existing metadata or create a new one."""
    meta_path = metadata_path(session_dir)
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    current_ts = now_iso()
    metadata = SessionMetadata(
        session_id=session_id,
        expert=expert,
        created_at=current_ts,
        updated_at=current_ts,
        schema_version=SCHEMA_VERSION,
        manual_tests_dir=str(manual_tests_dir),
        golden_features_dir=str(golden_features_dir),
        preset_features_dir=str(preset_features_dir) if preset_features_dir else None,
        results_dir=str(results_dir),
        evaluated_tests=0,
    )
    persist_metadata(session_dir, metadata.to_dict())
    return metadata.to_dict()


def persist_metadata(session_dir: Path, payload: dict[str, Any]) -> None:
    """Persist metadata with UTF-8 JSON formatting."""
    meta_path = metadata_path(session_dir)
    payload = dict(payload)
    payload["updated_at"] = now_iso()
    with meta_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def append_evaluation(session_dir: Path, record: dict[str, Any]) -> None:
    """Append record into evaluations.jsonl."""
    eval_path = evaluations_path(session_dir)
    with eval_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False))
        file.write("\n")


def load_latest_evaluations_by_test(session_dir: Path) -> dict[str, dict[str, Any]]:
    """Read jsonl and return latest record for each test_id."""
    eval_path = evaluations_path(session_dir)
    latest: dict[str, dict[str, Any]] = {}
    if not eval_path.exists():
        return latest

    with eval_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            test_id = payload.get("test_id")
            if test_id:
                latest[test_id] = payload
    return latest


def write_summary_csv(session_dir: Path, evaluations: dict[str, dict[str, Any]]) -> None:
    """Write compact summary for quick analysis."""
    rows = []
    for test_id, record in sorted(evaluations.items()):
        semantic = record.get("semantic_accuracy", {})
        matching = record.get("step_matching_precision", {})
        coverage = record.get("coverage_completeness", {})
        candidate = record.get("candidate", {})
        rows.append(
            {
                "test_id": test_id,
                "saved_at": record.get("saved_at", ""),
                "expert": record.get("expert", ""),
                "candidate_source": candidate.get("source", ""),
                "candidate_feature_path": candidate.get("feature_path", ""),
                "is_golden_candidate": candidate.get("is_golden_candidate", False),
                "semantic_weighted_score": semantic.get("weighted_score", 0),
                "semantic_is_correct": semantic.get("is_semantically_correct", False),
                "step_matching_precision": matching.get("precision", 0),
                "coverage_completeness": coverage.get("completeness", 0),
                "overall_comment": record.get("overall_comment", ""),
            }
        )

    csv_path = summary_path(session_dir)
    headers = [
        "test_id",
        "saved_at",
        "expert",
        "candidate_source",
        "candidate_feature_path",
        "is_golden_candidate",
        "semantic_weighted_score",
        "semantic_is_correct",
        "step_matching_precision",
        "coverage_completeness",
        "overall_comment",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def compute_aggregates(evaluations: dict[str, dict[str, Any]]) -> dict[str, float]:
    """Compute top-level aggregate values shown in UI."""
    if not evaluations:
        return {
            "semantic_accuracy": 0.0,
            "step_matching_precision": 0.0,
            "coverage_completeness": 0.0,
        }

    total = len(evaluations)
    semantic_correct = 0
    matching_sum = 0.0
    coverage_sum = 0.0

    for record in evaluations.values():
        semantic = record.get("semantic_accuracy", {})
        matching = record.get("step_matching_precision", {})
        coverage = record.get("coverage_completeness", {})

        if semantic.get("is_semantically_correct"):
            semantic_correct += 1
        matching_sum += float(matching.get("precision", 0.0))
        coverage_sum += float(coverage.get("completeness", 0.0))

    return {
        "semantic_accuracy": round(semantic_correct / total, 4),
        "step_matching_precision": round(matching_sum / total, 4),
        "coverage_completeness": round(coverage_sum / total, 4),
    }

