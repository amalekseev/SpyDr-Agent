import uuid
from collections.abc import AsyncGenerator

import streamlit as st
from langchain_core.messages import AIMessage

from src.api.dependencies import agent
from src.api.models import AgentResponse
from src.configs import global_config
from src.utils.streaming import langgraph_event_map

_CUSTOM_META_TYPES = {"text", "artifact"}

# ---------------------------------------------------------------------------
# Project helpers
# ---------------------------------------------------------------------------

_NO_PROJECT = "(без проекта)"


def _available_projects() -> list[str]:
    """Return project names from config (may be empty)."""
    projects = global_config.get("projects") or {}
    return list(projects.keys())


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------


async def _astream_agent_response(user_text: str) -> AsyncGenerator[AgentResponse, None]:
    """Stream agent events using graph.astream and normalize to AgentResponse."""
    graph_input: dict = {"messages": [{"role": "user", "content": user_text}]}

    graph_config = {
        "configurable": {
            "thread_id": st.session_state.thread_id,
            "project_id": st.session_state.get("project_id") or "",
            "validation_enabled": st.session_state.get("validation_enabled", False),
            "max_validation_iterations": st.session_state.get("max_validation_iterations", 3),
        },
    }

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

        yield AgentResponse(type=response_type, content=chunk.content)


async def _astream_text(
    user_text: str,
    artifact_placeholder: st.delta_generator.DeltaGenerator,
) -> AsyncGenerator[str, None]:
    """Async generator that yields text for st.write_stream.

    Artifact events dynamically update *artifact_placeholder* in the sidebar.
    """
    status_placeholder = st.info("⏳ Думаю...")

    async for response in _astream_agent_response(user_text):
        if response.type == "text":
            status_placeholder.empty()
            yield response.content
        elif response.type == "status":
            status_placeholder.info(f"⏳ {response.content}")
        elif response.type == "artifact":
            st.session_state.last_artifact = response.content
            artifact_placeholder.markdown(
                f"```gherkin\n{response.content}```"
            )

    status_placeholder.empty()


# ---------------------------------------------------------------------------
# Page config & session state init
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SpyDR Agent", page_icon="🕷️",
    initial_sidebar_state="auto",
    layout="centered",
)
st.title("SpyDR Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "last_artifact" not in st.session_state:
    st.session_state.last_artifact = ""
if "project_id" not in st.session_state:
    st.session_state.project_id = ""

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # --- Project selector ---
    projects = _available_projects()
    if projects:
        options = [_NO_PROJECT] + projects
        current = st.session_state.project_id
        default_idx = options.index(current) if current in options else 0

        selected = st.selectbox("Проект", options, index=default_idx)
        chosen_project = "" if selected == _NO_PROJECT else selected

        # If user changed the project, reset the session
        if chosen_project != st.session_state.project_id:
            st.session_state.project_id = chosen_project
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.last_artifact = ""
            st.rerun()

    st.subheader("Feature")
    artifact_slot = st.empty()    
    artifact_slot.markdown(
        f"```gherkin\n{st.session_state.last_artifact}```"
    )
    if st.session_state.last_artifact:
        st.download_button(
            label="Скачать .feature",
            data=st.session_state.last_artifact,
            file_name="feature.feature",
            icon=":material/download:",
            mime="text/plain",
        )
    st.divider()
    st.caption("Валидация")
    st.session_state.validation_enabled = st.toggle(
        "Валидация feature", value=st.session_state.get("validation_enabled", False)
    )
    st.session_state.max_validation_iterations = st.number_input(
        "Макс. итераций",
        min_value=1,
        max_value=10,
        value=st.session_state.get("max_validation_iterations", 3),
        disabled=not st.session_state.validation_enabled,
    )
    st.divider()
    st.caption("Сессия")
    if st.button("Очистить чат"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.last_artifact = ""
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Введите сообщение..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_response = st.write_stream(
            _astream_text(prompt, artifact_slot)
        )

    st.session_state.messages.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": full_response},
    ])
    st.rerun()
