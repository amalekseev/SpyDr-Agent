"""Convenience launcher for the Streamlit metrics app."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run expert metrics Streamlit app")
    parser.add_argument("--manual-tests-dir", default="manual_tests/tests")
    parser.add_argument("--golden-features-dir", default="golden_features")
    parser.add_argument("--preset-features-dir", default=None)
    parser.add_argument("--results-dir", default="metrics_results")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--expert", default=None)
    parser.add_argument("--llm-provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--rag-top-k", type=int, default=None)
    parser.add_argument("--steps-file", default="baseline/steps.json")
    parser.add_argument("--server-port", type=int, default=8501)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    app_path = repo_root / "metrics_app" / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.server_port),
        "--",
        "--manual-tests-dir",
        args.manual_tests_dir,
        "--golden-features-dir",
        args.golden_features_dir,
        "--results-dir",
        args.results_dir,
        "--steps-file",
        args.steps_file,
    ]

    optional_pairs = [
        ("--preset-features-dir", args.preset_features_dir),
        ("--session-id", args.session_id),
        ("--expert", args.expert),
        ("--llm-provider", args.llm_provider),
        ("--model", args.model),
        ("--embedding-model", args.embedding_model),
        ("--db-url", args.db_url),
    ]
    for key, value in optional_pairs:
        if value:
            cmd.extend([key, str(value)])

    if args.rag_top_k is not None:
        cmd.extend(["--rag-top-k", str(args.rag_top_k)])

    return subprocess.call(cmd, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())

