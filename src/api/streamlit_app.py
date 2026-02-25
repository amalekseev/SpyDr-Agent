import uuid
from collections.abc import AsyncGenerator

import streamlit as st
from langchain_core.messages import AIMessage

from src.api.dependencies import agent
from src.api.models import AgentResponse
from src.utils.streaming import langgraph_event_map

_CUSTOM_META_TYPES = {"text", "artifact"}


async def _astream_agent_response(user_text: str) -> AsyncGenerator[AgentResponse, None]:
    """Stream agent events using graph.astream and normalize to AgentResponse."""
    graph_input = {"messages": [{"role": "user", "content": user_text}]}
    graph_config = {"configurable": {"thread_id": st.session_state.thread_id}}

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

with st.sidebar:
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
