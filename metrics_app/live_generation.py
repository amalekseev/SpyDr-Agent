"""Live feature generation integration with baseline pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from baseline.core.pipeline import run_pipeline


def generate_live_feature(
    *,
    manual_test_path: Path,
    output_dir: Path,
    model: str,
    llm_provider: str,
    db_url: str | None,
    rag_top_k: int,
    embedding_model: str,
    steps_file: Path | None = None,
) -> tuple[Path | None, str | None, dict[str, Any]]:
    """
    Run baseline pipeline for a single manual test and return generated feature path.

    Returns:
        (generated_feature_path, error_text, pipeline_result_payload)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="metrics_live_input_") as tmp_dir_name:
        tmp_input_dir = Path(tmp_dir_name)
        tmp_manual_test_path = tmp_input_dir / manual_test_path.name
        shutil.copy2(manual_test_path, tmp_manual_test_path)

        try:
            payload = run_pipeline(
                input_dir=str(tmp_input_dir),
                output_dir=str(output_dir),
                steps_file=str(steps_file) if steps_file else None,
                model=model,
                llm_provider=llm_provider,
                db_url=db_url,
                rag_top_k=rag_top_k,
                embedding_model=embedding_model,
                reindex_steps=False,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - defensive error path
            return None, str(exc), {}

    candidate_path = output_dir / f"{manual_test_path.stem}.feature"
    if not candidate_path.exists():
        return None, "Pipeline finished without generated feature file.", payload
    return candidate_path, None, payload

