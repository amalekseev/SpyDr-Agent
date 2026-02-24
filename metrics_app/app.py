"""Streamlit app for expert metric annotation."""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

try:
    from metrics_app.data_loader import (
        list_manual_tests,
        map_feature_files_by_stem,
        read_text,
        resolve_path,
    )
    from metrics_app.live_generation import generate_live_feature
    from metrics_app.models import (
        CandidateInfo,
        CoverageChecklist,
        EvaluationRecord,
        SemanticChecklist,
        StepMatchingChecklist,
    )
    from metrics_app.storage import (
        append_evaluation,
        compute_aggregates,
        ensure_session_dir,
        load_latest_evaluations_by_test,
        load_or_create_metadata,
        persist_metadata,
        sanitize_session_id,
        write_summary_csv,
    )
except ImportError:
    import sys

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from metrics_app.data_loader import (
        list_manual_tests,
        map_feature_files_by_stem,
        read_text,
        resolve_path,
    )
    from metrics_app.live_generation import generate_live_feature
    from metrics_app.models import (
        CandidateInfo,
        CoverageChecklist,
        EvaluationRecord,
        SemanticChecklist,
        StepMatchingChecklist,
    )
    from metrics_app.storage import (
        append_evaluation,
        compute_aggregates,
        ensure_session_dir,
        load_latest_evaluations_by_test,
        load_or_create_metadata,
        persist_metadata,
        sanitize_session_id,
        write_summary_csv,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Expert metrics evaluation app")
    parser.add_argument("--manual-tests-dir", default="manual_tests/tests")
    parser.add_argument("--golden-features-dir", default="golden_features")
    parser.add_argument("--preset-features-dir", default=None)
    parser.add_argument("--results-dir", default="metrics_results")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--expert", default=os.getenv("USER", "expert"))
    parser.add_argument("--llm-provider", default=os.getenv("BASELINE_LLM_PROVIDER", "openai"))
    parser.add_argument("--model", default=os.getenv("BASELINE_MODEL", "gpt-4.1-nano"))
    parser.add_argument("--embedding-model", default=os.getenv("BASELINE_EMBEDDING_MODEL", "text-embedding-3-large"))
    parser.add_argument("--db-url", default=os.getenv("BASELINE_RAG_DB_URL"))
    parser.add_argument("--rag-top-k", type=int, default=5)
    parser.add_argument("--steps-file", default="steps.json")
    parser.add_argument(
        "--golden-sample-prob",
        type=float,
        default=float(os.getenv("METRICS_GOLDEN_SAMPLE_PROB", "0.5")),
    )
    args, _ = parser.parse_known_args(argv)
    args.repo_root = repo_root
    args.manual_tests_dir = resolve_path(args.manual_tests_dir, repo_root)
    args.golden_features_dir = resolve_path(args.golden_features_dir, repo_root)
    args.results_dir = resolve_path(args.results_dir, repo_root)
    args.steps_file = resolve_path(args.steps_file, repo_root)
    args.preset_features_dir = (
        resolve_path(args.preset_features_dir, repo_root) if args.preset_features_dir else None
    )
    args.golden_sample_prob = max(0.0, min(1.0, args.golden_sample_prob))
    return args


def ensure_runtime_state(config: argparse.Namespace) -> dict[str, Any]:
    if "runtime_state" in st.session_state:
        return st.session_state.runtime_state

    default_session = config.session_id
    if not default_session:
        default_session = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    default_session = sanitize_session_id(default_session)

    state = {
        "session_id": default_session,
        "expert": config.expert,
        "llm_provider": config.llm_provider,
        "model": config.model,
        "embedding_model": config.embedding_model,
        "db_url": config.db_url,
        "rag_top_k": config.rag_top_k,
        "live_candidates": {},
    }
    st.session_state.runtime_state = state
    return state


def metric_ratio_text(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_sidebar(
    *,
    runtime_state: dict[str, Any],
    config: argparse.Namespace,
    total_tests: int,
    evaluated_count: int,
    aggregates: dict[str, float],
) -> tuple[str, str]:
    st.sidebar.header("Session")
    runtime_state["session_id"] = sanitize_session_id(
        st.sidebar.text_input("Session ID", value=runtime_state["session_id"])
    )
    runtime_state["expert"] = st.sidebar.text_input("Expert", value=runtime_state["expert"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Progress")
    st.sidebar.write(f"Evaluated: {evaluated_count} / {total_tests}")
    st.sidebar.write(f"Semantic accuracy: {metric_ratio_text(aggregates['semantic_accuracy'])}")
    st.sidebar.write(
        f"Step matching precision: {metric_ratio_text(aggregates['step_matching_precision'])}"
    )
    st.sidebar.write(
        f"Coverage completeness: {metric_ratio_text(aggregates['coverage_completeness'])}"
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Live generation")
    runtime_state["llm_provider"] = st.sidebar.selectbox(
        "LLM provider",
        options=["openai", "gigachat"],
        index=0 if runtime_state["llm_provider"] == "openai" else 1,
    )
    runtime_state["model"] = st.sidebar.text_input("Model", value=runtime_state["model"])
    runtime_state["embedding_model"] = st.sidebar.text_input(
        "Embedding model", value=runtime_state["embedding_model"]
    )
    runtime_state["db_url"] = st.sidebar.text_input(
        "RAG DB URL",
        value=runtime_state["db_url"] or "",
        help="Required for live generation.",
    )
    runtime_state["rag_top_k"] = st.sidebar.number_input(
        "RAG top-k",
        min_value=1,
        max_value=100,
        step=1,
        value=int(runtime_state["rag_top_k"]),
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Data paths")
    st.sidebar.caption(f"Manual tests: `{config.manual_tests_dir}`")
    st.sidebar.caption(f"Golden features: `{config.golden_features_dir}`")
    if config.preset_features_dir:
        st.sidebar.caption(f"Preset features: `{config.preset_features_dir}`")
    else:
        st.sidebar.caption("Preset features: not set")
    st.sidebar.caption(f"Results root: `{config.results_dir}`")
    return runtime_state["session_id"], runtime_state["expert"]


def render_text_comparison(*, manual_test_text: str, candidate_feature_text: str | None) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Manual test (.txt)")
        st.code(manual_test_text, language="text")
    with right:
        st.subheader("Feature for evaluation (.feature)")
        if candidate_feature_text is None:
            st.info("Feature is not available for this test.")
        else:
            st.code(candidate_feature_text, language="gherkin")


def choose_assignment(
    *,
    metadata: dict[str, Any],
    test_id: str,
    session_id: str,
    golden_sample_prob: float,
) -> str:
    assignments = metadata.setdefault("assignments", {})
    if test_id in assignments:
        return assignments[test_id]
    draw = random.Random(f"{session_id}:{test_id}").random()
    selected = "golden" if draw < golden_sample_prob else "generated"
    assignments[test_id] = selected
    return selected


def resolve_presented_candidate(
    *,
    test_id: str,
    assignment: str,
    manual_test_path: Path,
    golden_feature_path: Path | None,
    preset_by_stem: dict[str, Path],
    runtime_state: dict[str, Any],
    session_dir: Path,
    config: argparse.Namespace,
) -> tuple[Path | None, str | None, str | None, bool]:
    generated_path: Path | None = None
    generated_source: str | None = None
    generated_error: str | None = None

    if test_id in preset_by_stem:
        generated_path = preset_by_stem[test_id]
        generated_source = "generated_preset"
    else:
        live_dir = session_dir / "live_generated"
        cached_path_raw = runtime_state["live_candidates"].get(test_id)
        if cached_path_raw:
            cached_path = Path(cached_path_raw)
            if cached_path.exists():
                generated_path = cached_path
                generated_source = "generated_live"

        if generated_path is None:
            generated_path, generated_error, _ = generate_live_feature(
                manual_test_path=manual_test_path,
                output_dir=live_dir,
                model=runtime_state["model"],
                llm_provider=runtime_state["llm_provider"],
                db_url=runtime_state["db_url"] or None,
                rag_top_k=int(runtime_state["rag_top_k"]),
                embedding_model=runtime_state["embedding_model"],
                steps_file=config.steps_file,
            )
            if generated_path:
                runtime_state["live_candidates"][test_id] = str(generated_path)
                generated_source = "generated_live"

    if assignment == "golden" and golden_feature_path:
        return golden_feature_path, "golden", None, True
    if assignment == "generated" and generated_path:
        return generated_path, generated_source, generated_error, False

    # Fallbacks if chosen source is unavailable.
    if golden_feature_path:
        return golden_feature_path, "golden", generated_error, True
    if generated_path:
        return generated_path, generated_source, generated_error, False
    return None, None, generated_error or "No golden and no generated feature available.", False


def main() -> None:
    st.set_page_config(page_title="SpyDR Metrics App", layout="wide")
    st.title("SpyDR expert metrics collection")
    st.caption("Evaluate generated or preset .feature files against manual tests.")

    config = parse_args(sys.argv[1:])
    runtime_state = ensure_runtime_state(config)

    manual_tests = list_manual_tests(config.manual_tests_dir)
    if not manual_tests:
        st.error(f"No manual tests found in: {config.manual_tests_dir}")
        return

    golden_by_stem = map_feature_files_by_stem(config.golden_features_dir)
    preset_by_stem = (
        map_feature_files_by_stem(config.preset_features_dir) if config.preset_features_dir else {}
    )

    session_dir = ensure_session_dir(config.results_dir, runtime_state["session_id"])
    metadata = load_or_create_metadata(
        session_dir=session_dir,
        session_id=runtime_state["session_id"],
        expert=runtime_state["expert"],
        manual_tests_dir=config.manual_tests_dir,
        golden_features_dir=config.golden_features_dir,
        preset_features_dir=config.preset_features_dir,
        results_dir=config.results_dir,
    )
    metadata.setdefault("golden_sample_prob", config.golden_sample_prob)
    evaluations_by_test = load_latest_evaluations_by_test(session_dir)
    aggregates = compute_aggregates(evaluations_by_test)

    render_sidebar(
        runtime_state=runtime_state,
        config=config,
        total_tests=len(manual_tests),
        evaluated_count=len(evaluations_by_test),
        aggregates=aggregates,
    )

    # Refresh session path if user changed session id from sidebar.
    session_dir = ensure_session_dir(config.results_dir, runtime_state["session_id"])
    metadata = load_or_create_metadata(
        session_dir=session_dir,
        session_id=runtime_state["session_id"],
        expert=runtime_state["expert"],
        manual_tests_dir=config.manual_tests_dir,
        golden_features_dir=config.golden_features_dir,
        preset_features_dir=config.preset_features_dir,
        results_dir=config.results_dir,
    )
    metadata.setdefault("golden_sample_prob", config.golden_sample_prob)
    evaluations_by_test = load_latest_evaluations_by_test(session_dir)

    st.info(
        "Session folder: "
        f"`{session_dir}`  |  Files: `evaluations.jsonl`, `summary.csv`, `metadata.json`"
    )

    all_test_ids = [path.stem for path in manual_tests]
    pending_ids = [test_id for test_id in all_test_ids if test_id not in evaluations_by_test]
    show_all = st.checkbox("Show already evaluated tests", value=False)
    selectable_ids = all_test_ids if show_all else pending_ids

    if not selectable_ids:
        st.success("All tests are already evaluated in this session.")
        return

    test_id = st.selectbox("Choose manual test", options=selectable_ids)
    manual_test_path = config.manual_tests_dir / f"{test_id}.txt"
    golden_feature_path = golden_by_stem.get(test_id)
    manual_test_text = read_text(manual_test_path)

    st.markdown("---")
    assignment = choose_assignment(
        metadata=metadata,
        test_id=test_id,
        session_id=runtime_state["session_id"],
        golden_sample_prob=float(metadata.get("golden_sample_prob", config.golden_sample_prob)),
    )
    with st.spinner("Preparing feature for evaluation..."):
        candidate_feature_path, candidate_source, candidate_generation_error, is_golden_candidate = (
            resolve_presented_candidate(
                test_id=test_id,
                assignment=assignment,
                manual_test_path=manual_test_path,
                golden_feature_path=golden_feature_path,
                preset_by_stem=preset_by_stem,
                runtime_state=runtime_state,
                session_dir=session_dir,
                config=config,
            )
        )
    candidate_feature_text: str | None = (
        read_text(candidate_feature_path) if candidate_feature_path and candidate_feature_path.exists() else None
    )
    persist_metadata(session_dir, metadata)
    if candidate_generation_error:
        st.warning("Generated feature was unavailable for this test; fallback may be used.")

    st.markdown("---")
    render_text_comparison(
        manual_test_text=manual_test_text,
        candidate_feature_text=candidate_feature_text,
    )

    st.markdown("---")
    st.subheader("Expert checklist")
    with st.form(f"evaluation_form_{test_id}"):
        st.markdown("### Semantic accuracy")
        sem_col1, sem_col2, sem_col3, sem_col4, sem_col5 = st.columns(5)
        with sem_col1:
            sem_preconditions = st.select_slider(
                "Preconditions", options=[0.0, 0.5, 1.0], value=1.0
            )
        with sem_col2:
            sem_actions = st.select_slider("Actions", options=[0.0, 0.5, 1.0], value=1.0)
        with sem_col3:
            sem_checks = st.select_slider("Checks", options=[0.0, 0.5, 1.0], value=1.0)
        with sem_col4:
            sem_order = st.select_slider("Step order", options=[0.0, 0.5, 1.0], value=1.0)
        with sem_col5:
            sem_completeness = st.select_slider(
                "Scenario completeness", options=[0.0, 0.5, 1.0], value=1.0
            )
        sem_comment = st.text_area("Semantic comment", value="", height=70)

        st.markdown("### Step matching precision")
        sm_col1, sm_col2 = st.columns(2)
        with sm_col1:
            sm_total = st.number_input("Total generated steps", min_value=0, value=0, step=1)
        with sm_col2:
            sm_matched = st.number_input("Matched steps", min_value=0, value=0, step=1)
        sm_err_col1, sm_err_col2, sm_err_col3, sm_err_col4 = st.columns(4)
        with sm_err_col1:
            sm_wrong = st.number_input("Wrong step", min_value=0, value=0, step=1)
        with sm_err_col2:
            sm_close = st.number_input("Close step", min_value=0, value=0, step=1)
        with sm_err_col3:
            sm_missing = st.number_input("Missing step definition", min_value=0, value=0, step=1)
        with sm_err_col4:
            sm_dropped = st.number_input("Dropped source step", min_value=0, value=0, step=1)
        sm_comment = st.text_area("Step matching comment", value="", height=70)

        st.markdown("### Coverage completeness")
        cov_col1, cov_col2 = st.columns(2)
        with cov_col1:
            cov_total = st.number_input("Total source steps", min_value=0, value=0, step=1)
        with cov_col2:
            cov_covered = st.number_input("Covered steps", min_value=0, value=0, step=1)
        cov_err_col1, cov_err_col2, cov_err_col3, cov_err_col4 = st.columns(4)
        with cov_err_col1:
            cov_no_match = st.number_input("No matching step reason", min_value=0, value=0, step=1)
        with cov_err_col2:
            cov_parse = st.number_input("Parse error reason", min_value=0, value=0, step=1)
        with cov_err_col3:
            cov_merged = st.number_input("Merged steps reason", min_value=0, value=0, step=1)
        with cov_err_col4:
            cov_redundant = st.number_input("Redundant step reason", min_value=0, value=0, step=1)
        cov_comment = st.text_area("Coverage comment", value="", height=70)

        overall_comment = st.text_area("Overall comment", value="", height=90)
        save_clicked = st.form_submit_button("Save and move to next")

    if save_clicked:
        if candidate_feature_path is None:
            st.error("Select/generate a candidate .feature before saving.")
            return
        if sm_matched > sm_total:
            st.error("Matched steps cannot exceed total generated steps.")
            return
        if cov_covered > cov_total:
            st.error("Covered steps cannot exceed total source steps.")
            return

        semantic = SemanticChecklist(
            preconditions=float(sem_preconditions),
            actions=float(sem_actions),
            checks=float(sem_checks),
            step_order=float(sem_order),
            scenario_completeness=float(sem_completeness),
            comment=sem_comment.strip(),
        )
        matching = StepMatchingChecklist(
            total_generated_steps=int(sm_total),
            matched_steps=int(sm_matched),
            wrong_step_count=int(sm_wrong),
            close_step_count=int(sm_close),
            missing_step_definition_count=int(sm_missing),
            dropped_source_step_count=int(sm_dropped),
            comment=sm_comment.strip(),
        )
        coverage = CoverageChecklist(
            total_source_steps=int(cov_total),
            covered_steps=int(cov_covered),
            no_matching_step_reason_count=int(cov_no_match),
            parse_error_reason_count=int(cov_parse),
            merged_steps_reason_count=int(cov_merged),
            redundant_step_reason_count=int(cov_redundant),
            comment=cov_comment.strip(),
        )

        record = EvaluationRecord(
            session_id=runtime_state["session_id"],
            expert=runtime_state["expert"],
            test_id=test_id,
            manual_test_path=str(manual_test_path),
            golden_feature_path=str(golden_feature_path) if golden_feature_path else None,
            candidate=CandidateInfo(
                source=candidate_source or "unknown",
                feature_path=str(candidate_feature_path),
                is_golden_candidate=is_golden_candidate,
                generation_model=runtime_state["model"] if candidate_source == "generated_live" else None,
                generation_provider=runtime_state["llm_provider"] if candidate_source == "generated_live" else None,
                generation_error=candidate_generation_error,
            ),
            semantic_accuracy=semantic,
            step_matching_precision=matching,
            coverage_completeness=coverage,
            overall_comment=overall_comment.strip(),
        )
        append_evaluation(session_dir, record.to_dict())

        latest_evaluations = load_latest_evaluations_by_test(session_dir)
        write_summary_csv(session_dir, latest_evaluations)
        metadata["expert"] = runtime_state["expert"]
        metadata["evaluated_tests"] = len(latest_evaluations)
        persist_metadata(session_dir, metadata)

        st.success("Saved successfully.")
        st.rerun()


if __name__ == "__main__":
    main()

