"""Menu Categories, Items, Variants, and Stock Schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MenuItemVariantBase(BaseModel):
    variant_type: str  # size, spice_level, topping
    variant_name: str
    price_delta: float = 0.0


class MenuItemVariantCreate(MenuItemVariantBase):
    menu_item_id: int


class MenuItemVariantResponse(MenuItemVariantBase):
    id: int
    menu_item_id: int

    model_config = ConfigDict(from_attributes=True)


class MenuItemStockUpdate(BaseModel):
    menu_item_id: int
    branch_id: int
    stock_quantity: int


class MenuItemStockResponse(BaseModel):
    id: int
    menu_item_id: int
    branch_id: int
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    category_id: int
    variants: Optional[List[MenuItemVariantBase]] = None
    initial_stock: Optional[int] = 50


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    is_available: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    id: int
    category_id: int
    variants: List[MenuItemVariantResponse] = []
    # Stock info for the queried branch (or default if unqueried)
    stock_quantity: Optional[int] = None
    effective_available: bool = True  # is_available and stock_quantity > 0

    model_config = ConfigDict(from_attributes=True)


class MenuCategoryBase(BaseModel):
    name: str
    branch_id: int


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryResponse(MenuCategoryBase):
    id: int
    items: List[MenuItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
