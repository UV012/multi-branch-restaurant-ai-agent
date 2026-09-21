"""Staff Menu and Inventory Management Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.security import get_current_staff
from backend.app.database import get_db
from backend.app.models.menu import MenuCategory, MenuItem, MenuItemStock, MenuItemVariant
from backend.app.models.user import StaffUser
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

router = APIRouter(prefix="/staff/menu", tags=["Staff Menu & Inventory Management"])


# Categories
@router.get("/categories", response_model=List[MenuCategoryResponse])
async def list_categories(
    branch_id: Optional[int] = Query(None),
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List menu categories for a branch."""
    b_id = current_staff.branch_id or branch_id or 1
    stmt = (
        select(MenuCategory)
        .where(MenuCategory.branch_id == b_id)
        .options(selectinload(MenuCategory.items).selectinload(MenuItem.variants))
        .order_by(MenuCategory.id.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/categories", response_model=MenuCategoryResponse)
async def create_category(
    payload: MenuCategoryCreate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create a new menu category."""
    if current_staff.branch_id and payload.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    cat = MenuCategory(branch_id=payload.branch_id, name=payload.name)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


# Items
@router.post("/items", response_model=MenuItemResponse)
async def create_item(
    payload: MenuItemCreate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create a new menu item and initialize its stock."""
    # Find category to know branch_id
    cat_res = await db.execute(select(MenuCategory).where(MenuCategory.id == payload.category_id))
    cat = cat_res.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")

    if current_staff.branch_id and cat.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    item = MenuItem(
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        base_price=payload.base_price,
        is_available=payload.is_available,
    )
    db.add(item)
    await db.flush()

    # Add variants if any
    if payload.variants:
        for v in payload.variants:
            var = MenuItemVariant(
                menu_item_id=item.id,
                variant_type=v.variant_type,
                variant_name=v.variant_name,
                price_delta=v.price_delta,
            )
            db.add(var)

    # Initialize stock
    stock = MenuItemStock(
        menu_item_id=item.id,
        branch_id=cat.branch_id,
        stock_quantity=payload.initial_stock if payload.initial_stock is not None else 50,
    )
    db.add(stock)

    await db.commit()
    await db.refresh(item)

    return MenuItemResponse(
        id=item.id,
        category_id=item.category_id,
        name=item.name,
        description=item.description,
        base_price=item.base_price,
        is_available=item.is_available,
        stock_quantity=stock.stock_quantity,
        effective_available=item.is_available and (stock.stock_quantity > 0),
        variants=[],
    )


@router.patch("/items/{item_id}", response_model=MenuItemResponse)
async def update_item(
    item_id: int,
    payload: MenuItemUpdate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update item details or toggle availability."""
    stmt = (
        select(MenuItem)
        .where(MenuItem.id == item_id)
        .options(
            selectinload(MenuItem.category),
            selectinload(MenuItem.variants),
            selectinload(MenuItem.stocks),
        )
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    if current_staff.branch_id and item.category.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.base_price is not None:
        item.base_price = payload.base_price
    if payload.is_available is not None:
        item.is_available = payload.is_available

    await db.commit()
    await db.refresh(item)

    stock_val = item.stocks[0].stock_quantity if item.stocks else 0
    return MenuItemResponse(
        id=item.id,
        category_id=item.category_id,
        name=item.name,
        description=item.description,
        base_price=item.base_price,
        is_available=item.is_available,
        stock_quantity=stock_val,
        effective_available=item.is_available and (stock_val > 0),
        variants=[
            MenuItemVariantResponse(
                id=v.id,
                menu_item_id=v.menu_item_id,
                variant_type=v.variant_type,
                variant_name=v.variant_name,
                price_delta=v.price_delta,
            )
            for v in item.variants
        ],
    )


# Stock Management
@router.put("/stock", response_model=MenuItemStockResponse)
async def update_stock(
    payload: MenuItemStockUpdate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update or restock quantity for a menu item at a branch."""
    if current_staff.branch_id and payload.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    if payload.stock_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative.")

    stmt = select(MenuItemStock).where(
        MenuItemStock.menu_item_id == payload.menu_item_id,
        MenuItemStock.branch_id == payload.branch_id,
    )
    res = await db.execute(stmt)
    stock = res.scalar_one_or_none()

    if not stock:
        stock = MenuItemStock(
            menu_item_id=payload.menu_item_id,
            branch_id=payload.branch_id,
            stock_quantity=payload.stock_quantity,
        )
        db.add(stock)
    else:
        stock.stock_quantity = payload.stock_quantity

    await db.commit()
    await db.refresh(stock)
    return stock
