"""
Утилиты для стриминга ответов агентов.
"""
from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer

langgraph_event_map = {
    "messages": "text",
    "custom": "status"
}

def set_status(status: str, namespace: str = "agent") -> None:
    """Отправляет статус в стрим."""
    writer = get_stream_writer()
    writer((AIMessage(content=status), namespace))
