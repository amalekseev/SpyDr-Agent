"""PostgreSQL + pgvector storage for BDD step retrieval."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row

from .constants import DEFAULT_EMBEDDING_MODEL
from .tracing import get_tracer

TRACER = get_tracer(__name__)


@dataclass
class StepRAGStore:
    """Storage and search helper over BDD steps."""

    db_url: str
    client: OpenAI
    embedding_model: str = DEFAULT_EMBEDDING_MODEL

    def ensure_schema(self) -> None:
        """Initialize extension, table and indexes required for vector search."""
        with TRACER.start_as_current_span("baseline.rag.ensure_schema"):
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS bdd_steps (
                            step_id TEXT PRIMARY KEY,
                            step_type TEXT NOT NULL,
                            pattern TEXT NOT NULL,
                            placeholders_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                            docstring TEXT NULL,
                            source_file TEXT NULL,
                            function_name TEXT NULL,
                            line_number INTEGER NULL,
                            embedding vector(1536) NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    )
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_bdd_steps_type ON bdd_steps(step_type)"
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_bdd_steps_embedding
                        ON bdd_steps
                        USING ivfflat (embedding vector_cosine_ops)
                        """
                    )
                conn.commit()

    def upsert_steps(self, steps: list[dict[str, Any]], verbose: bool = False) -> int:
        """Upsert all parsed steps and refresh their embeddings."""
        if not steps:
            return 0
        if verbose:
            print(f"  [rag] Индексация шагов: {len(steps)} шт.")
        inserted = 0
        with TRACER.start_as_current_span("baseline.rag.upsert_steps") as span:
            span.set_attribute("rag.steps_count", len(steps))
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    for step in steps:
                        started_at = time.perf_counter()
                        embedding = self._embed_step(step)
                        cur.execute(
                            """
                            INSERT INTO bdd_steps (
                                step_id, step_type, pattern, placeholders_json, docstring,
                                source_file, function_name, line_number, embedding, updated_at
                            ) VALUES (
                                %(step_id)s, %(step_type)s, %(pattern)s, %(placeholders)s, %(docstring)s,
                                %(source_file)s, %(function_name)s, %(line_number)s,
                                %(embedding)s::vector, now()
                            )
                            ON CONFLICT (step_id) DO UPDATE SET
                                step_type = EXCLUDED.step_type,
                                pattern = EXCLUDED.pattern,
                                placeholders_json = EXCLUDED.placeholders_json,
                                docstring = EXCLUDED.docstring,
                                source_file = EXCLUDED.source_file,
                                function_name = EXCLUDED.function_name,
                                line_number = EXCLUDED.line_number,
                                embedding = EXCLUDED.embedding,
                                updated_at = now()
                            """,
                            {
                                "step_id": step["step_id"],
                                "step_type": step["type"],
                                "pattern": step["pattern"],
                                "placeholders": json.dumps(step.get("placeholders", []), ensure_ascii=False),
                                "docstring": step.get("docstring"),
                                "source_file": step.get("source_file"),
                                "function_name": step.get("function_name"),
                                "line_number": step.get("line_number"),
                                "embedding": _vector_literal(embedding),
                            },
                        )
                        inserted += 1
                        if verbose and inserted % 50 == 0:
                            elapsed = time.perf_counter() - started_at
                            print(
                                f"  [rag] Обработано {inserted}/{len(steps)} (последний шаг за {elapsed:.2f}s)"
                            )
                conn.commit()
            span.set_attribute("rag.steps_upserted", inserted)
        if verbose:
            print("  [rag] Индексация завершена")
        return inserted

    def search_steps(
        self, *, query: str, step_type: str | None, top_k: int = 8, verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Run semantic retrieval over stored step embeddings."""
        with TRACER.start_as_current_span("baseline.rag.search_steps") as span:
            span.set_attribute("rag.top_k", top_k)
            span.set_attribute("rag.step_type", step_type or "any")
            span.set_attribute("rag.query_preview", query[:200])
            started_at = time.perf_counter()
            embedding = self._embed_text(query)
            where_clause = "WHERE step_type = %(step_type)s" if step_type else ""
            sql = f"""
                SELECT
                    step_id, step_type, pattern, placeholders_json, docstring,
                    source_file, function_name, line_number,
                    (1 - (embedding <=> %(embedding)s::vector)) AS score
                FROM bdd_steps
                {where_clause}
                ORDER BY embedding <=> %(embedding)s::vector
                LIMIT %(top_k)s
            """
            with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    params: dict[str, Any] = {
                        "embedding": _vector_literal(embedding),
                        "top_k": top_k,
                    }
                    if step_type:
                        params["step_type"] = step_type.lower()
                    cur.execute(sql, params)
                    rows = cur.fetchall()
            if verbose:
                elapsed = time.perf_counter() - started_at
                print(f"  [rag] Поиск кандидатов завершен за {elapsed:.2f}s")
            results: list[dict[str, Any]] = []
            for row in rows:
                results.append(
                    {
                        "step_id": row["step_id"],
                        "type": row["step_type"],
                        "pattern": row["pattern"],
                        "placeholders": row["placeholders_json"] or [],
                        "docstring": row["docstring"],
                        "source_file": row["source_file"],
                        "function_name": row["function_name"],
                        "line_number": row["line_number"],
                        "score": float(row["score"]),
                    }
                )
            span.set_attribute("rag.results_count", len(results))
            return results

    def _embed_step(self, step: dict[str, Any]) -> list[float]:
        placeholders = ", ".join(p["name"] for p in step.get("placeholders", []))
        text = (
            f"type: {step.get('type', '')}\n"
            f"pattern: {step.get('pattern', '')}\n"
            f"placeholders: {placeholders}\n"
            f"doc: {step.get('docstring') or ''}\n"
            f"source: {step.get('source_file') or ''}"
        )
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding


def resolve_database_url(explicit_db_url: str | None = None) -> str:
    """Resolve DB connection string from explicit flag or environment."""
    if explicit_db_url:
        return explicit_db_url
    db_url = os.getenv("BASELINE_RAG_DB_URL") or os.getenv("CONNECTION_STRING") or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "URL базы данных не задан. Передайте --db-url или установите BASELINE_RAG_DB_URL."
        )
    return db_url


def _vector_literal(values: list[float]) -> str:
    """Format python list as pgvector textual literal."""
    return "[" + ",".join(f"{value:.12f}" for value in values) + "]"

