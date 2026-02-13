"""Phoenix/OpenTelemetry tracing helpers."""

from __future__ import annotations

import os
import socket
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

_TRACING_CONFIGURED = False


def setup_file_logging(log_dir: str = "logs") -> Path:
    """Initialize detailed file logging."""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    log_file = log_path / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Configure root logger for the 'baseline' namespace
    logger = logging.getLogger("baseline")
    logger.setLevel(logging.DEBUG)

    # File handler with detailed format
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Prevent propagation to parent loggers to avoid double logging if configured elsewhere
    logger.propagate = False

    return log_file


def setup_phoenix_tracing(
    *,
    enabled: bool,
    endpoint: Optional[str],
    service_name: str,
) -> None:
    """Initialize OTLP exporter to Phoenix once per process."""
    global _TRACING_CONFIGURED
    if not enabled or _TRACING_CONFIGURED:
        return

    phoenix_endpoint = endpoint or os.getenv("PHOENIX_COLLECTOR_ENDPOINT") or "http://127.0.0.1:6006/v1/traces"
    if not _is_endpoint_reachable(phoenix_endpoint):
        print(
            "[tracing] Phoenix endpoint недоступен, tracing отключен: "
            f"{phoenix_endpoint}. Запустите Phoenix и повторите."
        )
        return

    # Optional imports so non-tracing mode does not require OTEL packages at runtime.
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True


def get_tracer(name: str):
    """Get tracer from active provider."""
    from opentelemetry import trace

    return trace.get_tracer(name)


def _is_endpoint_reachable(endpoint: str) -> bool:
    """Check if OTLP endpoint host:port is reachable."""
    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port
    if not host:
        return False
    if not port:
        port = 443 if parsed.scheme == "https" else 80
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False

