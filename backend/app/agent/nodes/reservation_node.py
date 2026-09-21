"""Reservation Flow LangGraph Node with Auto-Confirm and DB-Level Exclusion Guard."""

from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any, Dict
from langchain_core.messages import AIMessage

from backend.app.agent.llm import extract_json_from_text, ollama_client
from backend.app.agent.tools.table_tools import check_table_availability_and_book


async def reservation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle table booking with real-time table availability check and auto-confirm."""
    branch_id = state.get("branch_id")
    customer_id = state.get("customer_id")
    messages = state.get("messages", [])
    user_msg = messages[-1].content.strip() if messages else ""
    user_lower = user_msg.lower()

    # 1. Parse reservation parameters from message
    sys_prompt = f"""You are a restaurant reservation detail extractor.
Current date reference: 2026-09-16.
Extract the booking details from the customer message:
"{user_msg}"

Output a JSON object with this exact schema:
{{
  "party_size": <int or null>,
  "date": "<YYYY-MM-DD or null>",
  "time": "<HH:MM in 24-hour format or null>",
  "seating_area": "indoor" | "outdoor" | "rooftop" | "any",
  "notes": "<string or null>"
}}

Output ONLY valid JSON.
"""
    raw_llm = await ollama_client.generate(prompt=user_msg, system_prompt=sys_prompt)
    extracted = extract_json_from_text(raw_llm) or {}

    # Merge with existing draft if present
    draft = state.get("reservation_draft") or {}
    party_size = extracted.get("party_size") or draft.get("party_size")
    date_str = extracted.get("date") or draft.get("date")
    time_str = extracted.get("time") or draft.get("time")
    seating_area = extracted.get("seating_area") or draft.get("seating_area") or "indoor"
    notes = extracted.get("notes") or draft.get("notes")

    # Regex heuristic fallbacks for common phrases
    if not party_size:
        size_match = re.search(r"(?:table\s+for|party\s+of|for)\s+(\d+)", user_lower)
        if size_match:
            party_size = int(size_match.group(1))

    if not time_str:
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", user_lower)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            ampm = time_match.group(3).lower()
            if ampm == "pm" and hr < 12:
                hr += 12
            elif ampm == "am" and hr == 12:
                hr = 0
            time_str = f"{hr:02d}:{mn:02d}"

    if not date_str:
        if "today" in user_lower or "tonight" in user_lower:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        elif "tomorrow" in user_lower:
            date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    # Check for seating area preference keywords
    if "outdoor" in user_lower or "patio" in user_lower or "garden" in user_lower:
        seating_area = "outdoor"
    elif "rooftop" in user_lower or "terrace" in user_lower:
        seating_area = "rooftop"
    elif "indoor" in user_lower:
        seating_area = "indoor"

    # 2. Check if we need more information from the customer
    missing_fields = []
    if not party_size:
        missing_fields.append("how many guests (party size)")
    if not date_str:
        missing_fields.append("what date (e.g. today, tomorrow, or YYYY-MM-DD)")
    if not time_str:
        missing_fields.append("what time (e.g. 7:00 PM)")

    if missing_fields:
        prompt_reply = (
            f"I'd be glad to help you book a table! To check our availability, could you please tell me "
            f"{', and '.join(missing_fields)}? Also let me know if you prefer indoor, outdoor, or rooftop seating."
        )
        return {
            **state,
            "active_flow": "reservation",
            "reservation_draft": {
                "party_size": party_size,
                "date": date_str,
                "time": time_str,
                "seating_area": seating_area,
                "notes": notes,
            },
            "last_reply": prompt_reply,
            "messages": [AIMessage(content=prompt_reply)],
        }

    # 3. All info collected: parse datetime and check availability + auto-confirm
    try:
        start_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        # Fallback to evening time if malformed
        start_datetime = datetime.now(timezone.utc).replace(hour=19, minute=0, second=0, microsecond=0)

    # Call availability and auto-confirm tool (guarded by PostgreSQL exclusion constraint)
    res_result = await check_table_availability_and_book(
        customer_id=customer_id,
        branch_id=branch_id,
        start_time=start_datetime,
        party_size=party_size,
        duration_minutes=90,
        seating_area=seating_area,
        notes=notes,
    )

    if res_result.get("success"):
        res_id = res_result["reservation_id"]
        table_label = res_result["table_label"]
        area = res_result["seating_area"].capitalize()
        dt_display = res_result["date"]
        tm_display = res_result["time"]
        branch_name = res_result["branch_name"]

        reply = (
            f"✅ **Reservation Confirmed!**\n\n"
            f"• Reservation #{res_id}\n"
            f"• Branch: {branch_name}\n"
            f"• Table: {table_label} ({area} seating)\n"
            f"• Date & Time: {dt_display} at {tm_display} (90 mins)\n"
            f"• Party Size: {party_size} guests\n"
            f"• Status: Confirmed\n\n"
            f"We look forward to hosting you! You can manage or check your booking anytime."
        )
        return {
            **state,
            "active_flow": "none",
            "reservation_draft": None,
            "reservation_id": res_id,
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }
    else:
        # Table unavailable or race-condition conflict caught gracefully
        error_msg = res_result.get("error", "No tables available.")
        reply = f"❌ {error_msg}"
        return {
            **state,
            "active_flow": "reservation",
            "reservation_draft": {
                "party_size": party_size,
                "date": date_str,
                "time": None,  # Reset time so user can pick another slot
                "seating_area": seating_area,
                "notes": notes,
            },
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }
