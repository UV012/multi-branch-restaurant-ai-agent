"""Schemas Registry."""

from backend.app.schemas.auth import (
    CustomerLoginRequest,
    CustomerRegisterRequest,
    CustomerResponse,
    StaffLoginRequest,
    StaffResponse,
    TokenResponse,
)
from backend.app.schemas.branch import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    TableCreate,
    TableResponse,
    TableUpdate,
)
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemStockResponse,
    MenuItemStockUpdate,
    MenuItemUpdate,
    MenuItemVariantCreate,
    MenuItemVariantResponse,
)
from backend.app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from backend.app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    ReservationUpdate,
)

__all__ = [
    "CustomerLoginRequest",
    "CustomerRegisterRequest",
    "CustomerResponse",
    "StaffLoginRequest",
    "StaffResponse",
    "TokenResponse",
    "BranchCreate",
    "BranchResponse",
    "BranchUpdate",
    "TableCreate",
    "TableResponse",
    "TableUpdate",
    "ChatRequest",
    "ChatResponse",
    "MenuCategoryCreate",
    "MenuCategoryResponse",
    "MenuItemCreate",
    "MenuItemResponse",
    "MenuItemStockResponse",
    "MenuItemStockUpdate",
    "MenuItemUpdate",
    "MenuItemVariantCreate",
    "MenuItemVariantResponse",
    "OrderCreate",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderResponse",
    "OrderStatusUpdate",
    "ReservationCreate",
    "ReservationResponse",
    "ReservationUpdate",
]
