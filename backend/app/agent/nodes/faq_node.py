"""FAQ Node for Branch Details and Policies."""

from typing import Any, Dict
from langchain_core.messages import AIMessage

from backend.app.agent.tools.faq_tools import get_branch_faq


async def faq_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve hardcoded/seeded branch hours, address, phone, and policies."""
    branch_id = state.get("branch_id")
    faq_data = await get_branch_faq(branch_id)

    if "error" in faq_data:
        reply = faq_data["error"]
    else:
        policies = faq_data.get("policies", {})
        reply = (
            f"ℹ️ **Information for {faq_data['branch_name']}:**\n\n"
            f"• 📍 **Address:** {faq_data['address']}\n"
            f"• 📞 **Phone:** {faq_data['phone']}\n"
            f"• ⏰ **Hours:** {faq_data['opening_hours']}\n"
            f"• 🚗 **Parking:** {policies.get('parking', 'Available')}\n"
            f"• 👔 **Dress Code:** {policies.get('dress_code', 'Casual')}\n"
            f"• 💳 **Payment:** {policies.get('payment_methods', 'Cash or card at counter/delivery')}\n"
            f"• 🛵 **Delivery:** {policies.get('delivery_radius', 'Standard local radius')}\n\n"
            f"Would you like to browse the menu or reserve a table?"
        )

    return {
        **state,
        "active_flow": "none",
        "last_reply": reply,
        "messages": [AIMessage(content=reply)],
    }
