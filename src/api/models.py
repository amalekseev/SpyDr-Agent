from typing import Literal, Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Унифицированный ответ агента"""
    type: Literal["text", "status"]
    content: Optional[str]
