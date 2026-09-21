"""Order and OrderItem Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = 1
    selected_variants: Optional[List[Dict[str, Any]]] = None
    item_notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    selected_variants: Optional[List[Dict[str, Any]]] = None
    item_notes: Optional[str] = None
    menu_item_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    branch_id: int
    order_type: str = "dine_in"  # "dine_in", "takeaway", "delivery"
    delivery_address: Optional[str] = None
    special_notes: Optional[str] = None
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: str  # placed, preparing, ready, delivered, cancelled


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    branch_id: int
    order_type: str
    status: str
    delivery_address: Optional[str] = None
    special_notes: Optional[str] = None
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    branch_name: Optional[str] = None
    customer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
