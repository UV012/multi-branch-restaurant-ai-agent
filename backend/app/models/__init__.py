"""Database models registry."""

from backend.app.database import Base
from backend.app.models.branch import Branch, Table
from backend.app.models.menu import MenuCategory, MenuItem, MenuItemVariant, MenuItemStock
from backend.app.models.order import Order, OrderItem
from backend.app.models.reservation import Reservation
from backend.app.models.user import Customer, StaffUser

__all__ = [
    "Base",
    "Branch",
    "Table",
    "MenuCategory",
    "MenuItem",
    "MenuItemVariant",
    "MenuItemStock",
    "Order",
    "OrderItem",
    "Reservation",
    "Customer",
    "StaffUser",
]
