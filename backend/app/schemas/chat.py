"""Chat API Request and Response Schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    branch_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    active_flow: Optional[str] = None
    order_id: Optional[int] = None
    reservation_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None
