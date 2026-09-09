from pydantic import BaseModel
from typing import List, Optional, Any


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    stations: Optional[List[Any]] = None  # optional real station data from Django
    user_info: Optional[dict] = None      # optional logged in user info


class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]


class ChatTurn(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class AgentBookingRequest(BaseModel):
    user_id: str
    message: str
    history: List[ChatTurn] = []   # prior turns in this chat session


class AgentBookingResponse(BaseModel):
    response: str
    booking_id: Optional[int] = None
    payment: Optional[dict] = None