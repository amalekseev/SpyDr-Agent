"""
Утилиты для стриминга ответов агентов.
"""
from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer

langgraph_event_map = {
    "messages": "text",
    "custom": "status"
}

def set_status(status: str) -> None:
    """Отправляет статус в стрим."""
    writer = get_stream_writer()
    writer((AIMessage(content=status), "status"))


def stream_text(text: str) -> None:
    """Отправляет текст напрямую в стрим как сообщение ассистента."""
    writer = get_stream_writer()
    writer((AIMessage(content=text), "text"))


def stream_feature_written(path: str) -> None:
    """Уведомляет клиент, что feature-файл записан на диск."""
    writer = get_stream_writer()
    writer((AIMessage(content=path), "feature_written"))
