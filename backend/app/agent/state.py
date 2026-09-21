"""Agent State Definitions for LangGraph."""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """LangGraph conversation state persistent across customer sessions."""

    # Chat history
    messages: Annotated[List[BaseMessage], add_messages]

    # Customer Context
    customer_id: int
    customer_name: str

    # Branch Context
    branch_id: Optional[int]
    branch_name: Optional[str]

    # Current Flow State
    active_flow: Optional[str]  # "none", "branch_select", "order", "reservation", "status", "faq"

    # Order in progress
    order_draft: Optional[Dict[str, Any]]
    # Reservation in progress
    reservation_draft: Optional[Dict[str, Any]]

    # Response to return to the user
    last_reply: Optional[str]
    order_id: Optional[int]
    reservation_id: Optional[int]
    extra_data: Optional[Dict[str, Any]]
