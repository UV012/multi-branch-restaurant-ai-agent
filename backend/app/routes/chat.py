"""Customer Chat Endpoint Powered by LangGraph and Ollama DeepSeek R1."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.checkpointer import get_checkpointer
from backend.app.agent.graph import build_restaurant_graph
from backend.app.auth.security import get_current_customer
from backend.app.database import get_db
from backend.app.models.branch import Branch
from backend.app.models.user import Customer
from backend.app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("chat")
router = APIRouter(prefix="/chat", tags=["Customer Chat Agent"])


@router.post("", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
):
    """Send message to LangGraph conversational agent and receive structured response."""
    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    # Determine branch
    branch_id = payload.branch_id
    branch_name: Optional[str] = None
    if branch_id:
        branch_res = await db.execute(select(Branch).where(Branch.id == branch_id))
        branch_obj = branch_res.scalar_one_or_none()
        if branch_obj:
            branch_name = branch_obj.name

    # Thread ID for persistent memory: customer_id + branch_id
    thread_suffix = f"branch_{branch_id}" if branch_id else "global"
    thread_id = f"customer_{current_customer.id}_{thread_suffix}"
    config = {"configurable": {"thread_id": thread_id}}

    workflow = build_restaurant_graph()

    # Run workflow with shared PostgreSQL checkpointer
    try:
        app = workflow.compile(checkpointer=checkpointer)

        # Retrieve existing state or initialize new
        current_state = await app.aget_state(config)
        existing_values = current_state.values if current_state else {}

        input_state = {
            "messages": [HumanMessage(content=user_text)],
            "customer_id": current_customer.id,
            "customer_name": current_customer.name,
            "branch_id": branch_id or existing_values.get("branch_id"),
            "branch_name": branch_name or existing_values.get("branch_name"),
            "active_flow": existing_values.get("active_flow", "none"),
            "order_draft": existing_values.get("order_draft"),
            "reservation_draft": existing_values.get("reservation_draft"),
        }

        final_state = await app.ainvoke(input_state, config=config)

        reply_text = final_state.get("last_reply") or "I'm here to help with your orders and reservations! What would you like to do?"
        resolved_branch_id = final_state.get("branch_id")
        resolved_branch_name = final_state.get("branch_name")
        active_flow = final_state.get("active_flow")
        order_id = final_state.get("order_id")
        reservation_id = final_state.get("reservation_id")

        return ChatResponse(
            reply=reply_text,
            branch_id=resolved_branch_id,
            branch_name=resolved_branch_name,
            active_flow=active_flow,
            order_id=order_id,
            reservation_id=reservation_id,
            extra_data={
                "has_order_draft": bool(final_state.get("order_draft")),
                "has_reservation_draft": bool(final_state.get("reservation_draft")),
            },
        )

    except Exception as exc:
        logger.exception("Chat endpoint error: %s", exc)
        # Graceful error fallback
        return ChatResponse(
            reply=f"I encountered a temporary error processing your request. Please try again. ({str(exc)})",
            branch_id=branch_id,
            branch_name=branch_name,
            active_flow="none",
        )
