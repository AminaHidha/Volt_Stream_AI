from pydantic import BaseModel
from typing import List, Optional, Any


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    stations: Optional[List[Any]] = None  # ✅ real station data from Django
    user_info: Optional[dict] = None      # ✅ logged in user info


class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]