"""Branch Selector LangGraph Node."""

from typing import Any, Dict
from langchain_core.messages import AIMessage
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Branch


async def branch_selector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure conversation has a selected branch; prompt or resolve branch from user input."""
    # If branch is already set in state, continue
    if state.get("branch_id"):
        return state

    messages = state.get("messages", [])
    last_user_msg = messages[-1].content.strip().lower() if messages else ""

    # Fetch active branches
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Branch).where(Branch.is_active == True))
        branches = result.scalars().all()

    if not branches:
        reply = "Sorry, no restaurant branches are currently active. Please check back later."
        return {
            **state,
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }

    # Check if user mentioned branch name or number
    selected_branch = None
    for idx, b in enumerate(branches, start=1):
        if (
            str(b.id) in last_user_msg
            or str(idx) in last_user_msg.split()
            or b.name.lower() in last_user_msg
            or any(part in last_user_msg for part in b.name.lower().split() if len(part) > 3)
        ):
            selected_branch = b
            break

    if selected_branch:
        reply = f"Great! I've set your location to {selected_branch.name} ({selected_branch.address}). How can I help you today? You can browse our menu, place an order, book a table, or check order status."
        return {
            **state,
            "branch_id": selected_branch.id,
            "branch_name": selected_branch.name,
            "active_flow": "none",
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }

    # If not resolved, prompt user with branch options
    branch_list_str = "\n".join([f"• {idx}) {b.name} — {b.address}" for idx, b in enumerate(branches, start=1)])
    prompt_reply = (
        f"Welcome to our restaurant! Before we get started, which branch would you like to connect with?\n\n"
        f"{branch_list_str}\n\nPlease reply with the branch name or number."
    )
    return {
        **state,
        "active_flow": "branch_select",
        "last_reply": prompt_reply,
        "messages": [AIMessage(content=prompt_reply)],
    }
