"""PostgreSQL + pgvector storage for BDD step retrieval."""

from __future__ import annotations

import json
import os
import time
import logging
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .constants import DEFAULT_EMBEDDING_MODEL
from .tracing import get_tracer

TRACER = get_tracer(__name__)
LOGGER = logging.getLogger("baseline.rag")


@dataclass
class StepRAGStore:
    """Storage and search helper over BDD steps."""

    db_url: str
    client: Any
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    _embedding_dimension: int | None = None

    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension dynamically from the model."""
        if self._embedding_dimension is not None:
            return self._embedding_dimension
        # Make a test embedding call to get the actual dimension
        LOGGER.debug(f"Determining embedding dimension for model: {self.embedding_model}")
        test_embedding = self._embed_text("test")
        self._embedding_dimension = len(test_embedding)
        LOGGER.info(f"Detected embedding dimension: {self._embedding_dimension}")
        return self._embedding_dimension

    def ensure_schema(self) -> None:
        """Initialize extension, table and indexes required for vector search."""
        with TRACER.start_as_current_span("baseline.rag.ensure_schema") as span:
            LOGGER.debug(f"Ensuring schema in DB: {self.db_url.split('@')[-1] if '@' in self.db_url else '...'}")
            print(f"  [rag] Проверка схемы БД (URL: {self.db_url.split('@')[-1] if '@' in self.db_url else '...'})")
            embedding_dim = self._get_embedding_dimension()
            span.set_attribute("rag.embedding_dimension", embedding_dim)
            try:
                with psycopg.connect(self.db_url) as conn:
                    with conn.cursor() as cur:
                        LOGGER.debug("Setting up schemas and vector extension...")
                        print("  [rag] Подключение установлено, настройка схем и расширения vector...")
                        # Ensure schemas exist (though they should be created already)
                        cur.execute("CREATE SCHEMA IF NOT EXISTS ext")
                        cur.execute("CREATE SCHEMA IF NOT EXISTS spydr_ai")
                        
                        # Set search path to include our schemas
                        cur.execute("SET search_path TO spydr_ai, ext, public")
                        
                        # Create extension in ext schema
                        cur.execute("CREATE EXTENSION IF NOT EXISTS vector SCHEMA ext")
                        
                        # Create main table in spydr_ai (default schema now) if not exists
                        LOGGER.debug(f"Creating bdd_steps table with dimension {embedding_dim}...")
                        print(f"  [rag] Создание таблицы bdd_steps (dim={embedding_dim}) если не существует...")
                        cur.execute(
                            f"""
                            CREATE TABLE IF NOT EXISTS bdd_steps (
                                step_id TEXT PRIMARY KEY,
                                step_type TEXT NOT NULL,
                                pattern TEXT NOT NULL,
                                placeholders_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                                docstring TEXT NULL,
                                source_file TEXT NULL,
                                function_name TEXT NULL,
                                line_number INTEGER NULL,
                                requires_docstring BOOLEAN NOT NULL DEFAULT false,
                                requires_datatable BOOLEAN NOT NULL DEFAULT false,
                                embedding ext.vector({embedding_dim}) NOT NULL,
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                            )
                            """
                        )

                        # Add requires_docstring/requires_datatable columns if missing
                        # (for existing databases that don't have them yet).
                        for col, col_type in [
                            ("requires_docstring", "BOOLEAN NOT NULL DEFAULT false"),
                            ("requires_datatable", "BOOLEAN NOT NULL DEFAULT false"),
                        ]:
                            cur.execute(
                                """
                                SELECT 1 FROM information_schema.columns
                                WHERE table_schema = 'spydr_ai'
                                  AND table_name = 'bdd_steps'
                                  AND column_name = %(col)s
                                """,
                                {"col": col},
                            )
                            if not cur.fetchone():
                                LOGGER.info(f"Adding missing column {col} to bdd_steps...")
                                cur.execute(f"ALTER TABLE bdd_steps ADD COLUMN {col} {col_type}")
                        
                        LOGGER.debug("Creating index idx_bdd_steps_type...")
                        print("  [rag] Создание индекса idx_bdd_steps_type...")
                        cur.execute(
                            "CREATE INDEX IF NOT EXISTS idx_bdd_steps_type ON bdd_steps(step_type)"
                        )
                    conn.commit()
                LOGGER.info("DB schema is ready.")
                print("  [rag] Схема БД готова")
            except Exception as e:
                LOGGER.error(f"Error during schema initialization: {e}")
                print(f"  [rag] ОШИБКА при инициализации схемы: {e}")
                raise

    def clear_all(self) -> None:
        """Clear all stored steps."""
        LOGGER.warning("Clearing all steps from bdd_steps table.")
        print("  [rag] Очистка таблицы bdd_steps...")
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO spydr_ai, ext, public")
                    cur.execute("TRUNCATE TABLE bdd_steps")
                conn.commit()
            print("  [rag] Таблица очищена")
        except Exception as e:
            LOGGER.error(f"Error during table truncation: {e}")
            print(f"  [rag] ОШИБКА при очистке таблицы: {e}")
            raise

    def count_steps(self) -> int:
        """Return current number of indexed steps in storage."""
        try:
            with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO spydr_ai, ext, public")
                    cur.execute("SELECT COUNT(*) AS total FROM bdd_steps")
                    row = cur.fetchone() or {}
                    count = int(row.get("total") or 0)
                    LOGGER.debug(f"Current step count in DB: {count}")
                    return count
        except Exception as e:
            LOGGER.error(f"Error counting steps: {e}")
            print(f"  [rag] ОШИБКА при подсчете шагов: {e}")
            raise

    def upsert_steps(self, steps: list[dict[str, Any]], verbose: bool = False) -> int:
        """Upsert all parsed steps and refresh their embeddings."""
        if not steps:
            return 0
        
        LOGGER.info(f"Starting indexing of {len(steps)} steps.")
        # Always print start of indexing if not verbose, or more details if verbose
        print(f"  [rag] Начало индексации {len(steps)} шагов...")
        
        inserted = 0
        with TRACER.start_as_current_span("baseline.rag.upsert_steps") as span:
            span.set_attribute("rag.steps_count", len(steps))
            try:
                with psycopg.connect(self.db_url) as conn:
                    with conn.cursor() as cur:
                        # Ensure search_path is set
                        cur.execute("SET search_path TO spydr_ai, ext, public")
                        
                        last_log_time = time.perf_counter()
                        for idx, step in enumerate(steps, 1):
                            step_start = time.perf_counter()
                            try:
                                LOGGER.debug(f"Indexing step {idx}/{len(steps)}: {step.get('step_id')}")
                                embedding = self._embed_step(step)

                                # Serialize type: list -> comma-separated, string -> as-is.
                                step_type_raw = step.get("type", "")
                                if isinstance(step_type_raw, list):
                                    step_type_str = ",".join(sorted(step_type_raw))
                                else:
                                    step_type_str = str(step_type_raw)

                                cur.execute(
                                    """
                                    INSERT INTO bdd_steps (
                                        step_id, step_type, pattern, placeholders_json, docstring,
                                        source_file, function_name, line_number,
                                        requires_docstring, requires_datatable,
                                        embedding, updated_at
                                    ) VALUES (
                                        %(step_id)s, %(step_type)s, %(pattern)s, %(placeholders)s, %(docstring)s,
                                        %(source_file)s, %(function_name)s, %(line_number)s,
                                        %(requires_docstring)s, %(requires_datatable)s,
                                        %(embedding)s::ext.vector, now()
                                    )
                                    ON CONFLICT (step_id) DO UPDATE SET
                                        step_type = EXCLUDED.step_type,
                                        pattern = EXCLUDED.pattern,
                                        placeholders_json = EXCLUDED.placeholders_json,
                                        docstring = EXCLUDED.docstring,
                                        source_file = EXCLUDED.source_file,
                                        function_name = EXCLUDED.function_name,
                                        line_number = EXCLUDED.line_number,
                                        requires_docstring = EXCLUDED.requires_docstring,
                                        requires_datatable = EXCLUDED.requires_datatable,
                                        embedding = EXCLUDED.embedding,
                                        updated_at = now()
                                    """,
                                    {
                                        "step_id": step["step_id"],
                                        "step_type": step_type_str,
                                        "pattern": step["pattern"],
                                        "placeholders": json.dumps(step.get("placeholders", []), ensure_ascii=False),
                                        "docstring": step.get("docstring"),
                                        "source_file": step.get("source_file"),
                                        "function_name": step.get("function_name"),
                                        "line_number": step.get("line_number"),
                                        "requires_docstring": bool(step.get("requires_docstring")),
                                        "requires_datatable": bool(step.get("requires_datatable")),
                                        "embedding": _vector_literal(embedding),
                                    },
                                )
                                inserted += 1
                                
                                # Log progress every 5 steps or every 5 seconds to show it's alive
                                current_time = time.perf_counter()
                                if inserted % 5 == 0 or (current_time - last_log_time) > 5.0 or inserted == len(steps):
                                    elapsed = current_time - last_log_time
                                    LOGGER.info(f"Indexing progress: {inserted}/{len(steps)}")
                                    print(f"  [rag] Прогресс: {inserted}/{len(steps)} (последний блок за {elapsed:.2f}s)")
                                    last_log_time = current_time
                                    
                            except Exception as step_err:
                                LOGGER.error(f"Error processing step {step.get('step_id')}: {step_err}")
                                print(f"  [rag] ОШИБКА при обработке шага {step.get('step_id')}: {step_err}")
                                raise
                    conn.commit()
            except Exception as e:
                LOGGER.error(f"Critical error during indexing: {e}")
                print(f"  [rag] КРИТИЧЕСКАЯ ОШИБКА при индексации: {e}")
                raise
            span.set_attribute("rag.steps_upserted", inserted)
        
        LOGGER.info(f"Indexing completed: {inserted} steps.")
        print(f"  [rag] Индексация завершена: {inserted} шагов обработано")
        return inserted

    def search_steps(
        self, *, query: str, step_type: str | None, top_k: int = 8, verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Run semantic retrieval over stored step embeddings."""
        LOGGER.debug(f"Searching steps: query='{query}', type={step_type}, top_k={top_k}")
        with TRACER.start_as_current_span("baseline.rag.search_steps") as span:
            span.set_attribute("rag.top_k", top_k)
            span.set_attribute("rag.step_type", step_type or "any")
            span.set_attribute("rag.query_preview", query[:200])
            started_at = time.perf_counter()
            
            if verbose:
                print(f"  [rag] Поиск: '{query[:50]}...' (тип: {step_type or 'любой'})")
            
            try:
                embedding = self._embed_text(query)
            except Exception as e:
                LOGGER.error(f"Error creating query embedding: {e}")
                print(f"  [rag] ОШИБКА при создании эмбеддинга запроса: {e}")
                raise

            # step_type is stored as comma-separated list (e.g. "given,when,then").
            # Use ANY(string_to_array(...)) to match multi-type steps.
            if step_type:
                where_clause = "WHERE %(step_type)s = ANY(string_to_array(step_type, ','))"
            else:
                where_clause = ""

            sql = f"""
                SELECT
                    step_id, step_type, pattern, placeholders_json, docstring,
                    source_file, function_name, line_number,
                    requires_docstring, requires_datatable,
                    (1 - (embedding <=> %(embedding)s::ext.vector)) AS score
                FROM bdd_steps
                {where_clause}
                ORDER BY embedding <=> %(embedding)s::ext.vector
                LIMIT %(top_k)s
            """
            
            try:
                with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
                    with conn.cursor() as cur:
                        # Ensure search_path is set for the session
                        cur.execute("SET search_path TO spydr_ai, ext, public")
                        params: dict[str, Any] = {
                            "embedding": _vector_literal(embedding),
                            "top_k": top_k,
                        }
                        if step_type:
                            params["step_type"] = step_type.lower()
                        cur.execute(sql, params)
                        rows = cur.fetchall()
            except Exception as e:
                LOGGER.error(f"Error searching DB: {e}")
                print(f"  [rag] ОШИБКА при поиске в БД: {e}")
                raise

            if verbose:
                elapsed = time.perf_counter() - started_at
                print(f"  [rag] Найдено кандидатов: {len(rows)} (за {elapsed:.2f}s)")
            
            results: list[dict[str, Any]] = []
            for row in rows:
                # Parse step_type back to list or string for the agent.
                raw_type = row["step_type"]
                if "," in raw_type:
                    type_value: Any = raw_type.split(",")
                else:
                    type_value = raw_type

                results.append(
                    {
                        "step_id": row["step_id"],
                        "type": type_value,
                        "pattern": row["pattern"],
                        "placeholders": row["placeholders_json"] or [],
                        "docstring": row["docstring"],
                        "source_file": row["source_file"],
                        "function_name": row["function_name"],
                        "line_number": row["line_number"],
                        "requires_docstring": row.get("requires_docstring", False),
                        "requires_datatable": row.get("requires_datatable", False),
                        "score": float(row["score"]),
                    }
                )
            LOGGER.debug(f"Found {len(results)} candidates.")
            span.set_attribute("rag.results_count", len(results))
            return results

    # Hard ceiling (in characters) for text sent to the embedding API.
    # text-embedding-3-large supports 8 191 tokens ≈ 25-30K chars for English,
    # but Cyrillic is tokenised less efficiently, so we stay conservative.
    _MAX_EMBED_CHARS: int = 8_000
    # Max characters kept from a step docstring before embedding.
    _MAX_DOCSTRING_CHARS: int = 500

    def _embed_step(self, step: dict[str, Any]) -> list[float]:
        placeholders = ", ".join(p["name"] for p in step.get("placeholders", []))
        step_type = step.get("type", "")
        if isinstance(step_type, list):
            type_str = ",".join(sorted(step_type))
        else:
            type_str = str(step_type)

        raw_doc = step.get("docstring") or ""
        if len(raw_doc) > self._MAX_DOCSTRING_CHARS:
            LOGGER.debug(
                f"Truncating docstring for step {step.get('step_id')}: "
                f"{len(raw_doc)} → {self._MAX_DOCSTRING_CHARS} chars"
            )
            raw_doc = raw_doc[: self._MAX_DOCSTRING_CHARS] + "…"

        text = (
            f"type: {type_str}\n"
            f"pattern: {step.get('pattern', '')}\n"
            f"placeholders: {placeholders}\n"
            f"doc: {raw_doc}\n"
            f"source: {step.get('source_file') or ''}"
        )
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        if len(text) > self._MAX_EMBED_CHARS:
            LOGGER.warning(
                f"Embedding text truncated: {len(text)} → {self._MAX_EMBED_CHARS} chars"
            )
            text = text[: self._MAX_EMBED_CHARS]
        try:
            LOGGER.debug(f"Calling embedding API for model: {self.embedding_model}")
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            embedding = response.data[0].embedding
            LOGGER.debug(f"Received embedding of length {len(embedding)}")
            return embedding
        except Exception as e:
            LOGGER.error(f"Error calling embedding API: {e}")
            print(f"  [rag] ОШИБКА при вызове API эмбеддингов: {e}")
            raise


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
