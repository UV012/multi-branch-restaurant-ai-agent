"""Customer Orders and Reservations History Routes."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.security import get_current_customer
from backend.app.database import get_db
from backend.app.models.order import Order
from backend.app.models.reservation import Reservation
from backend.app.models.user import Customer
from backend.app.schemas.order import OrderResponse
from backend.app.schemas.reservation import ReservationResponse

router = APIRouter(tags=["Customer Activity"])


@router.get("/orders/me", response_model=List[OrderResponse])
async def get_my_orders(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get all orders placed by the current customer across branches."""
    stmt = (
        select(Order)
        .where(Order.customer_id == current_customer.id)
        .options(
            selectinload(Order.items),
            selectinload(Order.branch),
        )
        .order_by(Order.created_at.desc())
    )
    res = await db.execute(stmt)
    orders = res.scalars().all()

    # Format response
    output = []
    for o in orders:
        output.append(
            OrderResponse(
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
                customer_name=current_customer.name,
            )
        )
    return output


@router.get("/reservations/me", response_model=List[ReservationResponse])
async def get_my_reservations(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get all table reservations booked by the current customer across branches."""
    stmt = (
        select(Reservation)
        .where(Reservation.customer_id == current_customer.id)
        .options(
            selectinload(Reservation.table),
            selectinload(Reservation.branch),
        )
        .order_by(Reservation.start_time.desc())
    )
    res = await db.execute(stmt)
    reservations = res.scalars().all()

    output = []
    for r in reservations:
        output.append(
            ReservationResponse(
                id=r.id,
                customer_id=r.customer_id,
                branch_id=r.branch_id,
                table_id=r.table_id,
                party_size=r.party_size,
                start_time=r.start_time,
                end_time=r.end_time,
                duration_minutes=r.duration_minutes,
                seating_area_preference=r.seating_area_preference,
                status=r.status,
                notes=r.notes,
                created_at=r.created_at,
                table_label=r.table.label if r.table else None,
                branch_name=r.branch.name if r.branch else None,
                customer_name=current_customer.name,
            )
        )
    return output
