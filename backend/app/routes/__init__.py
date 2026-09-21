"""Routes registry."""

from backend.app.routes.auth import router as auth_router
from backend.app.routes.branches import router as branches_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.customer_orders import router as customer_orders_router
from backend.app.routes.staff_auth import router as staff_auth_router
from backend.app.routes.staff_branches import router as staff_branches_router
from backend.app.routes.staff_menu import router as staff_menu_router
from backend.app.routes.staff_orders import router as staff_orders_router
from backend.app.routes.staff_reservations import router as staff_reservations_router

__all__ = [
    "auth_router",
    "branches_router",
    "chat_router",
    "customer_orders_router",
    "staff_auth_router",
    "staff_branches_router",
    "staff_menu_router",
    "staff_orders_router",
    "staff_reservations_router",
]
