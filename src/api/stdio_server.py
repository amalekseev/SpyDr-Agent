"""JSON-lines stdio server for the SpyDR agent.

Reads JSON messages from stdin, runs the agent, writes JSON responses to stdout.
Designed to be launched as a subprocess by the GigaIDE plugin.

Usage::

    python -m src.api.stdio_server
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from typing import Any

from langchain_core.messages import AIMessage

from src.api.dependencies import agent
from src.api.models import AgentResponse
from src.configs import global_config
from src.utils.streaming import langgraph_event_map

logger = logging.getLogger(__name__)

_CUSTOM_META_TYPES = {"text", "feature_written", "status"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _available_projects() -> list[str]:
    """Return project names from config (may be empty)."""
    projects = global_config.get("projects") or {}
    return list(projects.keys())


def _emit(payload: dict[str, Any]) -> None:
    """Write a single JSON line to stdout and flush."""
    line = json.dumps(payload, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _emit_text(content: str) -> None:
    _emit({"type": "text", "content": content})


def _emit_status(content: str) -> None:
    _emit({"type": "status", "content": content})


def _emit_feature_written(path: str) -> None:
    _emit({"type": "feature_written", "path": path})


def _emit_error(content: str) -> None:
    _emit({"type": "error", "content": content})


def _emit_done() -> None:
    _emit({"type": "done"})


def _emit_projects(projects: list[str]) -> None:
    _emit({"type": "projects", "projects": projects})


# ---------------------------------------------------------------------------
# Agent streaming
# ---------------------------------------------------------------------------

async def _handle_chat(
    message: str,
    config: dict[str, Any],
    thread_id: str,
) -> None:
    """Run the agent and stream responses as JSON lines."""
    graph_input: dict = {"messages": [{"role": "user", "content": message}]}

    graph_config = {
        "configurable": {
            "thread_id": thread_id,
            "project_id": config.get("project_id", ""),
            "feature_file_path": config.get("feature_file_path", ""),
            "validation_enabled": config.get("validation_enabled", False),
            "max_validation_iterations": config.get("max_validation_iterations", 3),
        },
    }

    try:
        async for namespace, event, (chunk, meta) in agent.graph.astream(
            graph_input,
            config=graph_config,
            stream_mode=["messages", "custom"],
            subgraphs=True,
        ):
            if not isinstance(chunk, AIMessage) or not chunk.content:
                continue

            if isinstance(meta, str) and meta in _CUSTOM_META_TYPES:
                response_type = meta
            else:
                response_type = langgraph_event_map.get(event, "text")

            if response_type == "feature_written":
                _emit_feature_written(chunk.content)
            elif response_type == "status":
                _emit_status(chunk.content)
            else:
                _emit_text(chunk.content)

    except Exception as exc:
        logger.exception("Error during agent streaming")
        _emit_error(str(exc))

    _emit_done()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def _main_loop() -> None:
    """Read JSON lines from stdin and dispatch commands."""
    thread_id = str(uuid.uuid4())

    # Announce ready
    _emit({"type": "ready", "projects": _available_projects()})

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            _emit_error(f"Invalid JSON: {exc}")
            continue

        msg_type = msg.get("type", "")

        if msg_type == "chat":
            user_message = msg.get("message", "")
            config = msg.get("config", {})
            if not user_message:
                _emit_error("Empty message")
                _emit_done()
                continue
            await _handle_chat(user_message, config, thread_id)

        elif msg_type == "reset":
            thread_id = str(uuid.uuid4())
            _emit({"type": "session_reset", "thread_id": thread_id})

        elif msg_type == "list_projects":
            _emit_projects(_available_projects())

        else:
            _emit_error(f"Unknown message type: {msg_type}")


def main() -> None:
    """Entry point for ``python -m src.api.stdio_server``."""
    # Redirect logging to stderr so it doesn't interfere with JSON protocol
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    try:
        asyncio.run(_main_loop())
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    main()
