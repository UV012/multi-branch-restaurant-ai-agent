"""LangGraph StateGraph Definition and Execution."""

from typing import Any, Dict
from langgraph.graph import END, StateGraph

from backend.app.agent.nodes.branch_selector import branch_selector_node
from backend.app.agent.nodes.faq_node import faq_node
from backend.app.agent.nodes.intent_router import intent_router_node
from backend.app.agent.nodes.order_node import order_node
from backend.app.agent.nodes.reservation_node import reservation_node
from backend.app.agent.nodes.status_node import status_node
from backend.app.agent.state import AgentState


def route_intent(state: Dict[str, Any]) -> str:
    """Conditional edge router based on router decision."""
    next_dest = state.get("next_node", "end")
    if next_dest in ["branch_selector", "order", "reservation", "status", "faq"]:
        return next_dest
    return END


def build_restaurant_graph():
    """Build and compile LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("branch_selector", branch_selector_node)
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("order", order_node)
    workflow.add_node("reservation", reservation_node)
    workflow.add_node("status", status_node)
    workflow.add_node("faq", faq_node)

    # Set Entry Point
    workflow.set_entry_point("intent_router")

    # Add Conditional Routing from intent_router
    workflow.add_conditional_edges(
        "intent_router",
        route_intent,
        {
            "branch_selector": "branch_selector",
            "order": "order",
            "reservation": "reservation",
            "status": "status",
            "faq": "faq",
            END: END,
        },
    )

    # Leaf nodes terminate back to user
    workflow.add_edge("branch_selector", END)
    workflow.add_edge("order", END)
    workflow.add_edge("reservation", END)
    workflow.add_edge("status", END)
    workflow.add_edge("faq", END)

    return workflow


# Compiled graph builder
compiled_graph = build_restaurant_graph().compile()
