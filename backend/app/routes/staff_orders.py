"""Staff Orders Management Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.security import get_current_staff
from backend.app.database import get_db
from backend.app.models.menu import MenuItemStock
from backend.app.models.order import Order, OrderItem
from backend.app.models.user import StaffUser
from backend.app.schemas.order import OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/staff/orders", tags=["Staff Orders Management"])


def _format_order_response(o: Order) -> OrderResponse:
    return OrderResponse(
        id=o.id,
        customer_id=o.customer_id,
        branch_id=o.branch_id,
        order_type=o.order_type,
        status=o.status,
        delivery_address=o.delivery_address,
        special_notes=o.special_notes,
        total_amount=o.total_amount,
        created_at=o.created_at,
        updated_at=o.updated_at,
        items=[
            {
                "id": item.id,
                "order_id": item.order_id,
                "menu_item_id": item.menu_item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "selected_variants": item.selected_variants,
                "item_notes": item.item_notes,
            }
            for item in o.items
        ],
        branch_name=o.branch.name if o.branch else None,
        customer_name=o.customer.name if o.customer else None,
    )


@router.get("", response_model=List[OrderResponse])
async def list_staff_orders(
    branch_id: Optional[int] = Query(None),
    order_status: Optional[str] = Query(None, alias="status"),
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List orders, optionally filtered by branch and status."""
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.customer),
            selectinload(Order.branch),
        )
        .order_by(Order.created_at.desc())
    )

    # Scoping: if staff is branch-restricted, enforce their branch
    if current_staff.branch_id:
        stmt = stmt.where(Order.branch_id == current_staff.branch_id)
    elif branch_id:
        stmt = stmt.where(Order.branch_id == branch_id)

    if order_status:
        stmt = stmt.where(Order.status == order_status)

    res = await db.execute(stmt)
    orders = res.scalars().all()

    output = [_format_order_response(o) for o in orders]
    return output


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update order status (placed -> preparing -> ready -> delivered / cancelled)."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.customer),
            selectinload(Order.branch),
        )
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found.",
        )

    # Permission check if staff is branch-restricted
    if current_staff.branch_id and order.branch_id != current_staff.branch_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage orders for this branch.",
        )

    valid_statuses = ["placed", "preparing", "ready", "delivered", "cancelled"]
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}.",
        )

    # No-op guard: if payload.status == order.status already, skip all stock logic entirely
    if payload.status == order.status:
        return _format_order_response(order)

    # Stock reversal logic:
    # 1. On transition INTO "cancelled" (from any non-cancelled status):
    #    restore each item's quantity
    if order.status != "cancelled" and payload.status == "cancelled":
        for item in order.items:
            restore_stmt = (
                update(MenuItemStock)
                .where(
                    MenuItemStock.menu_item_id == item.menu_item_id,
                    MenuItemStock.branch_id == order.branch_id,
                )
                .values(stock_quantity=MenuItemStock.stock_quantity + item.quantity)
            )
            await db.execute(restore_stmt)

    # 2. On transition OUT of "cancelled" back to "placed" (un-cancel):
    #    re-decrement each item's quantity using the atomic conditional pattern
    elif order.status == "cancelled" and payload.status == "placed":
        failed_items = []
        for item in order.items:
            decrement_stmt = (
                update(MenuItemStock)
                .where(
                    MenuItemStock.menu_item_id == item.menu_item_id,
                    MenuItemStock.branch_id == order.branch_id,
                    MenuItemStock.stock_quantity >= item.quantity,
                )
                .values(stock_quantity=MenuItemStock.stock_quantity - item.quantity)
            )
            result = await db.execute(decrement_stmt)
            if result.rowcount != 1:
                item_name = item.menu_item.name if item.menu_item else f"Item #{item.menu_item_id}"
                failed_items.append(item_name)

        if failed_items:
            await db.rollback()
            unique_names = list(dict.fromkeys(failed_items))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot un-cancel order: insufficient stock for item(s): {', '.join(unique_names)}.",
            )

    elif order.status == "cancelled" and payload.status != "placed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A cancelled order can only be un-cancelled to 'placed' status.",
        )

    order.status = payload.status
    await db.commit()
    await db.refresh(order)

    return _format_order_response(order)

