"""PostgreSQL + pgvector storage for BDD step retrieval via LangChain PGVector."""

from __future__ import annotations

import json
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from .constants import DEFAULT_EMBEDDING_MODEL
from .tracing import get_tracer

TRACER = get_tracer(__name__)
LOGGER = logging.getLogger("baseline.rag")

COLLECTION_NAME = "bdd_steps"


def _langchain_connection_string(db_url: str) -> str:
    """Convert a plain postgresql:// URL to the psycopg driver format LangChain expects."""
    if db_url.startswith("postgresql+psycopg://"):
        return db_url
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


@dataclass
class StepRAGStore:
    """Storage and search helper over BDD steps using LangChain PGVector."""

    db_url: str
    client: Any
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    _store: PGVector | None = field(default=None, init=False, repr=False)
    _embeddings: OpenAIEmbeddings | None = field(default=None, init=False, repr=False)

    def _get_embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model=self.embedding_model)
        return self._embeddings

    def _get_store(self) -> PGVector:
        if self._store is None:
            conn_str = _langchain_connection_string(self.db_url)
            self._store = PGVector(
                embeddings=self._get_embeddings(),
                collection_name=COLLECTION_NAME,
                connection=conn_str,
                distance_strategy=DistanceStrategy.COSINE,
                use_jsonb=True,
                async_mode=False,
                create_extension=False,
            )
        return self._store

    def ensure_schema(self) -> None:
        """Ensure LangChain PGVector tables exist."""
        with TRACER.start_as_current_span("baseline.rag.ensure_schema"):
            LOGGER.debug(f"Ensuring schema in DB: {self.db_url.split('@')[-1] if '@' in self.db_url else '...'}")
            print(f"  [rag] Проверка схемы БД (URL: {self.db_url.split('@')[-1] if '@' in self.db_url else '...'})")
            try:
                self._get_store()
                LOGGER.info("DB schema is ready (LangChain PGVector).")
                print("  [rag] Схема БД готова (LangChain PGVector)")
            except Exception as e:
                LOGGER.error(f"Error during schema initialization: {e}")
                print(f"  [rag] ОШИБКА при инициализации схемы: {e}")
                raise

    def clear_all(self) -> None:
        """Clear all stored steps from the collection."""
        LOGGER.warning("Clearing all steps from LangChain PGVector collection.")
        print("  [rag] Очистка коллекции bdd_steps...")
        try:
            store = self._get_store()
            store.delete_collection()
            self._store = None
            print("  [rag] Коллекция очищена")
        except Exception as e:
            LOGGER.error(f"Error during collection clearing: {e}")
            print(f"  [rag] ОШИБКА при очистке коллекции: {e}")
            raise

    def count_steps(self) -> int:
        """Return current number of indexed steps in storage."""
        try:
            conn_str = _langchain_connection_string(self.db_url)
            import psycopg
            from psycopg.rows import dict_row
            raw_url = conn_str.replace("postgresql+psycopg://", "postgresql://", 1)
            with psycopg.connect(raw_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = %s
                        """,
                        (COLLECTION_NAME,),
                    )
                    row = cur.fetchone() or {}
                    count = int(row.get("total") or 0)
                    LOGGER.debug(f"Current step count in DB: {count}")
                    return count
        except Exception as e:
            LOGGER.error(f"Error counting steps: {e}")
            print(f"  [rag] ОШИБКА при подсчете шагов: {e}")
            raise

    def upsert_steps(self, steps: list[dict[str, Any]], verbose: bool = False) -> int:
        """Upsert all parsed steps into LangChain PGVector."""
        if not steps:
            return 0

        LOGGER.info(f"Starting indexing of {len(steps)} steps.")
        print(f"  [rag] Начало индексации {len(steps)} шагов...")

        inserted = 0
        with TRACER.start_as_current_span("baseline.rag.upsert_steps") as span:
            span.set_attribute("rag.steps_count", len(steps))

            store = self._get_store()
            last_log_time = time.perf_counter()

            for idx, step in enumerate(steps, 1):
                try:
                    LOGGER.debug(f"Indexing step {idx}/{len(steps)}: {step.get('step_id')}")

                    step_type_raw = step.get("type", "")
                    if isinstance(step_type_raw, list):
                        step_type_str = ",".join(sorted(step_type_raw))
                    else:
                        step_type_str = str(step_type_raw)

                    text = self._build_embed_text(step)

                    metadata = {
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
                    }

                    doc = Document(page_content=text, metadata=metadata)
                    store.add_documents([doc], ids=[step["step_id"]])
                    inserted += 1

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

            store = self._get_store()
            filter_dict = {}
            if step_type:
                filter_dict["step_type"] = step_type.lower()

            try:
                docs_with_scores = store.similarity_search_with_score(
                    query=query,
                    k=top_k,
                    filter=filter_dict if filter_dict else None,
                )
            except Exception as e:
                LOGGER.error(f"Error searching DB: {e}")
                print(f"  [rag] ОШИБКА при поиске в БД: {e}")
                raise

            if verbose:
                elapsed = time.perf_counter() - started_at
                print(f"  [rag] Найдено кандидатов: {len(docs_with_scores)} (за {elapsed:.2f}s)")

            results: list[dict[str, Any]] = []
            for doc, distance in docs_with_scores:
                meta = doc.metadata or {}

                raw_type = meta.get("step_type", "")
                if "," in raw_type:
                    type_value: Any = raw_type.split(",")
                else:
                    type_value = raw_type

                raw_placeholders = meta.get("placeholders", [])
                if isinstance(raw_placeholders, str):
                    try:
                        raw_placeholders = json.loads(raw_placeholders)
                    except (json.JSONDecodeError, TypeError):
                        raw_placeholders = []

                results.append(
                    {
                        "step_id": meta.get("step_id", ""),
                        "type": type_value,
                        "pattern": meta.get("pattern", ""),
                        "placeholders": raw_placeholders,
                        "docstring": meta.get("docstring"),
                        "source_file": meta.get("source_file"),
                        "function_name": meta.get("function_name"),
                        "line_number": meta.get("line_number"),
                        "requires_docstring": meta.get("requires_docstring", False),
                        "requires_datatable": meta.get("requires_datatable", False),
                        "score": round(1.0 - distance, 4),
                    }
                )
            LOGGER.debug(f"Found {len(results)} candidates.")
            span.set_attribute("rag.results_count", len(results))
            return results

    # Hard ceiling (in characters) for text sent to the embedding API.
    # text-embedding-3-large supports 8 191 tokens ~ 25-30K chars for English,
    # but Cyrillic is tokenised less efficiently, so we stay conservative.
    _MAX_EMBED_CHARS: int = 8_000
    _MAX_DOCSTRING_CHARS: int = 500

    def _build_embed_text(self, step: dict[str, Any]) -> str:
        """Build the text representation of a step for embedding."""
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
                f"{len(raw_doc)} -> {self._MAX_DOCSTRING_CHARS} chars"
            )
            raw_doc = raw_doc[: self._MAX_DOCSTRING_CHARS] + "…"

        text = (
            f"type: {type_str}\n"
            f"pattern: {step.get('pattern', '')}\n"
            f"placeholders: {placeholders}\n"
            f"doc: {raw_doc}\n"
            f"source: {step.get('source_file') or ''}"
        )
        if len(text) > self._MAX_EMBED_CHARS:
            LOGGER.warning(
                f"Embedding text truncated: {len(text)} -> {self._MAX_EMBED_CHARS} chars"
            )
            text = text[: self._MAX_EMBED_CHARS]
        return text

    def _embed_step(self, step: dict[str, Any]) -> list[float]:
        text = self._build_embed_text(step)
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        if len(text) > self._MAX_EMBED_CHARS:
            LOGGER.warning(
                f"Embedding text truncated: {len(text)} -> {self._MAX_EMBED_CHARS} chars"
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
