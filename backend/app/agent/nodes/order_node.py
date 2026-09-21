"""Order Flow LangGraph Node."""

import json
import re
from typing import Any, Dict
from langchain_core.messages import AIMessage

from backend.app.agent.llm import extract_json_from_text, ollama_client
from backend.app.agent.tools.menu_tools import format_menu_for_prompt, get_branch_menu_data
from backend.app.agent.tools.order_tools import create_order_atomic


async def order_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handles menu presentation, item selection, stock checks, order summary, and atomic creation."""
    branch_id = state.get("branch_id")
    customer_id = state.get("customer_id")
    messages = state.get("messages", [])
    user_msg = messages[-1].content.strip() if messages else ""
    user_lower = user_msg.lower()

    # 1. Handle menu browsing request
    if any(k in user_lower for k in ["what's on the menu", "show menu", "view menu", "see menu", "what do you have", "what pizzas"]):
        menu_text = await format_menu_for_prompt(branch_id)
        reply = (
            f"Here is our current menu with real-time availability:\n\n"
            f"{menu_text}\n\n"
            f"What would you like to order? (Please mention quantity, size/options, and order type: dine-in, takeaway, or delivery)"
        )
        return {
            **state,
            "active_flow": "order",
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }

    # 2. Check if user is confirming an existing order draft
    order_draft = state.get("order_draft")
    if order_draft and order_draft.get("awaiting_confirmation"):
        if any(w in user_lower for w in ["yes", "confirm", "place order", "go ahead", "sure", "yep", "ok", "okay"]):
            # Execute atomic order creation + stock decrement
            result = await create_order_atomic(
                customer_id=customer_id,
                branch_id=branch_id,
                order_type=order_draft.get("order_type", "dine_in"),
                items=order_draft.get("items", []),
                delivery_address=order_draft.get("delivery_address"),
                special_notes=order_draft.get("special_notes"),
            )

            if result.get("success"):
                order_id = result["order_id"]
                total = result["total_amount"]
                order_type = result["order_type"].replace("_", " ").title()
                reply = (
                    f"🎉 Excellent! Your order #{order_id} has been placed successfully!\n\n"
                    f"• Order Type: {order_type}\n"
                    f"• Total Amount: ${total:.2f}\n"
                    f"• Status: Placed (Preparing shortly)\n\n"
                    f"Payment will be handled at the counter or upon delivery (cash/card). Thank you for dining with us!"
                )
                return {
                    **state,
                    "active_flow": "none",
                    "order_draft": None,
                    "order_id": order_id,
                    "last_reply": reply,
                    "messages": [AIMessage(content=reply)],
                }
            else:
                # Stock error or validation error
                err_reply = f"❌ Could not place order: {result.get('error')}"
                return {
                    **state,
                    "active_flow": "order",
                    "order_draft": None,  # Reset draft so user can adjust
                    "last_reply": err_reply,
                    "messages": [AIMessage(content=err_reply)],
                }

        elif any(w in user_lower for w in ["no", "cancel", "change", "stop", "abort", "wait"]):
            cancel_reply = "Order cancelled. What else can I help you with?"
            return {
                **state,
                "active_flow": "none",
                "order_draft": None,
                "last_reply": cancel_reply,
                "messages": [AIMessage(content=cancel_reply)],
            }

    # 3. Extract items, quantities, variants, and order type from user message
    menu_data = await get_branch_menu_data(branch_id)
    menu_summary = await format_menu_for_prompt(branch_id)

    extraction_prompt = f"""You are an order extraction parser for a restaurant.
Extract the customer's order from their message based on this real menu:
{menu_summary}

Customer message: "{user_msg}"

Return a JSON object with this exact schema:
{{
  "items": [
    {{
      "menu_item_id": <int>,
      "name": "<string>",
      "quantity": <int>,
      "selected_variants": [{{"name": "<string>", "delta": <float>}}],
      "item_notes": "<string or null>"
    }}
  ],
  "order_type": "dine_in" | "takeaway" | "delivery",
  "delivery_address": "<string or null>",
  "special_notes": "<string or null>"
}}

If the message does not mention order_type, default to "dine_in".
If no menu item is ordered, return {{"items": []}}.
Output ONLY the JSON object.
"""
    raw_llm = await ollama_client.generate(prompt=user_msg, system_prompt=extraction_prompt)
    extracted = extract_json_from_text(raw_llm) or {}

    # Rule-based fallback extraction if LLM JSON parse yielded empty items
    items_to_order = extracted.get("items", [])
    if not items_to_order:
        # Match against menu items in menu_data
        for cat in menu_data.get("categories", []):
            for item in cat.get("items", []):
                item_name_lower = item["name"].lower()
                if item_name_lower in user_lower or any(word in user_lower for word in item_name_lower.split() if len(word) > 4):
                    # Find quantity
                    qty_match = re.search(r"(\d+)\s*(?:x\s*)?" + re.escape(item_name_lower[:4]), user_lower)
                    qty = int(qty_match.group(1)) if qty_match else 1
                    items_to_order.append({
                        "menu_item_id": item["id"],
                        "name": item["name"],
                        "quantity": qty,
                        "selected_variants": [],
                        "item_notes": None,
                    })

    if not items_to_order:
        reply = (
            f"I didn't quite catch which items you'd like to order. Here is our menu:\n\n"
            f"{menu_summary}\n\n"
            f"Please reply with the dish name and quantity (e.g., '2 Margherita Pizzas and 1 Lemonade, delivery to 123 Elm St')."
        )
        return {
            **state,
            "active_flow": "order",
            "last_reply": reply,
            "messages": [AIMessage(content=reply)],
        }

    # Determine order type and address
    order_type = extracted.get("order_type", "dine_in")
    if any(k in user_lower for k in ["deliver", "delivery", "home delivery"]):
        order_type = "delivery"
    elif any(k in user_lower for k in ["takeaway", "take out", "takeout", "pick up", "pickup"]):
        order_type = "takeaway"

    delivery_address = extracted.get("delivery_address")
    if order_type == "delivery" and not delivery_address:
        # Check if address was provided in message
        addr_match = re.search(r"(?:to|at)\s+([0-9]+\s+[A-Za-z0-9\s,.-]+(?:st|ave|rd|blvd|street|avenue|road|lane|apt|suite)?)", user_msg, re.IGNORECASE)
        if addr_match:
            delivery_address = addr_match.group(1).strip()
        else:
            ask_addr_reply = (
                f"I have your order ready, but for delivery I need your delivery address. "
                f"Please reply with your address (e.g., 'Delivery to 456 Maple Ave, Apt 2B')."
            )
            return {
                **state,
                "active_flow": "order",
                "order_draft": {
                    "items": items_to_order,
                    "order_type": "delivery",
                    "awaiting_address": True,
                },
                "last_reply": ask_addr_reply,
                "messages": [AIMessage(content=ask_addr_reply)],
            }

    # 4. Check stock availability for all items before confirmation!
    stock_errors = []
    items_map = {}
    for cat in menu_data.get("categories", []):
        for it in cat.get("items", []):
            items_map[it["id"]] = it

    total_est = 0.0
    summary_lines = []
    for it in items_to_order:
        m_item = items_map.get(it["menu_item_id"])
        if not m_item:
            continue
        req_qty = it.get("quantity", 1)
        avail_qty = m_item.get("stock_quantity", 0)

        if avail_qty < req_qty:
            if avail_qty == 0:
                stock_errors.append(f"• '{m_item['name']}' is currently out of stock.")
            else:
                shortfall = req_qty - avail_qty
                stock_errors.append(f"• '{m_item['name']}': only {avail_qty} available (requested {req_qty}, short by {shortfall}).")
            continue

        item_price = m_item["base_price"]
        for v in it.get("selected_variants", []):
            item_price += v.get("delta", 0.0)
        subtotal = item_price * req_qty
        total_est += subtotal
        summary_lines.append(f"  • {req_qty}x {m_item['name']} — ${subtotal:.2f}")

    if stock_errors:
        err_msg = (
            f"⚠️ Some items in your order have insufficient stock at this branch:\n\n"
            + "\n".join(stock_errors)
            + "\n\nPlease adjust the quantities or choose an alternative item from our menu."
        )
        return {
            **state,
            "active_flow": "order",
            "last_reply": err_msg,
            "messages": [AIMessage(content=err_msg)],
        }

    # 5. Present Order Summary and Ask for Explicit Confirmation
    order_type_display = order_type.replace("_", " ").title()
    summary_text = (
        f"📝 **Order Summary ({state.get('branch_name', 'Branch')}):**\n\n"
        + "\n".join(summary_lines)
        + f"\n\n**Order Type:** {order_type_display}\n"
        + (f"**Delivery Address:** {delivery_address}\n" if delivery_address else "")
        + f"**Estimated Total:** ${total_est:.2f}\n"
        + f"*(Payment is made at pickup/delivery via cash or card)*\n\n"
        + f"👉 **Please reply 'Yes' or 'Confirm' to place your order, or 'No' to make changes.**"
    )

    return {
        **state,
        "active_flow": "order",
        "order_draft": {
            "items": items_to_order,
            "order_type": order_type,
            "delivery_address": delivery_address,
            "total_estimated": total_est,
            "awaiting_confirmation": True,
        },
        "last_reply": summary_text,
        "messages": [AIMessage(content=summary_text)],
    }
