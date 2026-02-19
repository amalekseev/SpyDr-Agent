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

        with TRACER.start_as_current_span("baseline.rag.upsert_steps") as span:
            span.set_attribute("rag.steps_count", len(steps))
            store = self._get_store()

            documents: list[Document] = []
            ids: list[str] = []
            last_log_time = time.perf_counter()

            for idx, step in enumerate(steps, 1):
                placeholders = ", ".join(
                    p["name"] for p in step.get("placeholders", [])
                )
                page_content = (
                    f"type: {step.get('type', '')}\n"
                    f"pattern: {step.get('pattern', '')}\n"
                    f"placeholders: {placeholders}\n"
                    f"doc: {step.get('docstring') or ''}\n"
                    f"source: {step.get('source_file') or ''}"
                )
                metadata = {
                    "step_id": step["step_id"],
                    "step_type": step.get("type", ""),
                    "pattern": step.get("pattern", ""),
                    "placeholders": step.get("placeholders", []),
                    "docstring": step.get("docstring"),
                    "source_file": step.get("source_file"),
                    "function_name": step.get("function_name"),
                    "line_number": step.get("line_number"),
                }
                documents.append(Document(page_content=page_content, metadata=metadata))
                ids.append(step["step_id"])

                current_time = time.perf_counter()
                if idx % 50 == 0 or (current_time - last_log_time) > 5.0:
                    LOGGER.info(f"Prepared {idx}/{len(steps)} documents")
                    print(f"  [rag] Подготовлено документов: {idx}/{len(steps)}")
                    last_log_time = current_time

            try:
                batch_size = 100
                inserted = 0
                for i in range(0, len(documents), batch_size):
                    batch_docs = documents[i : i + batch_size]
                    batch_ids = ids[i : i + batch_size]
                    store.add_documents(batch_docs, ids=batch_ids)
                    inserted += len(batch_docs)
                    LOGGER.info(f"Indexing progress: {inserted}/{len(documents)}")
                    print(f"  [rag] Прогресс: {inserted}/{len(documents)}")
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
                results.append(
                    {
                        "step_id": meta.get("step_id", ""),
                        "type": meta.get("step_type", ""),
                        "pattern": meta.get("pattern", ""),
                        "placeholders": meta.get("placeholders", []),
                        "docstring": meta.get("docstring"),
                        "source_file": meta.get("source_file"),
                        "function_name": meta.get("function_name"),
                        "line_number": meta.get("line_number"),
                        "score": round(1.0 - distance, 4),
                    }
                )
            LOGGER.debug(f"Found {len(results)} candidates.")
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
