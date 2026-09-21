"""Intent Router Node for LangGraph."""

import json
from typing import Any, Dict
from langchain_core.messages import AIMessage

from backend.app.agent.llm import extract_json_from_text, ollama_client


async def intent_router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Route customer request based on active flow or LLM intent classification."""
    # If branch is not set, must route to branch selector first
    if not state.get("branch_id"):
        return {**state, "next_node": "branch_selector"}

    active_flow = state.get("active_flow", "none")
    messages = state.get("messages", [])
    if not messages:
        return {**state, "next_node": "general"}

    last_user_msg = messages[-1].content.strip().lower()

    # If currently in confirmation step for an order or reservation, keep in that node
    if active_flow == "order" and state.get("order_draft"):
        return {**state, "next_node": "order"}
    if active_flow == "reservation" and state.get("reservation_draft"):
        return {**state, "next_node": "reservation"}

    # Keyword fast path for reliability & speed
    if any(k in last_user_msg for k in ["order", "pizza", "pasta", "drink", "buy", "cart", "eat", "menu", "food", "tiramisu", "lemonade", "coke"]):
        # If user is asking about menu without placing order, order node handles menu display too
        return {**state, "next_node": "order"}

    if any(k in last_user_msg for k in ["reserve", "table", "book", "reservation", "seat"]):
        return {**state, "next_node": "reservation"}

    if any(k in last_user_msg for k in ["status", "where is", "track", "my order", "my reservation", "did my order"]):
        return {**state, "next_node": "status"}

    if any(k in last_user_msg for k in ["hour", "open", "close", "time", "address", "location", "where are", "phone", "park", "dress"]):
        return {**state, "next_node": "faq"}

    # Fallback to DeepSeek R1 classification
    sys_prompt = """You are an intent classification system for a restaurant AI assistant.
Classify the user's intent into EXACTLY ONE of the following JSON formats:
{"intent": "order"}
{"intent": "reservation"}
{"intent": "status"}
{"intent": "faq"}
{"intent": "general"}

Output ONLY valid JSON. Do not output conversational filler.
"""
    raw_response = await ollama_client.generate(prompt=last_user_msg, system_prompt=sys_prompt)
    parsed = extract_json_from_text(raw_response)
    intent = parsed.get("intent", "general") if parsed else "general"

    if intent in ["order", "reservation", "status", "faq"]:
        return {**state, "next_node": intent}

    # General greeting / fallback
    reply = "Hello! I can help you view our menu, order delicious food, book a table reservation, or check the status of your existing orders and bookings. What would you like to do?"
    return {
        **state,
        "next_node": "end",
        "last_reply": reply,
        "messages": [AIMessage(content=reply)],
    }
