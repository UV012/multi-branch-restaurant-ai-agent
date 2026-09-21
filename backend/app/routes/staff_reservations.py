"""Staff Reservations Management Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.security import get_current_staff
from backend.app.database import get_db
from backend.app.models.reservation import Reservation
from backend.app.models.user import StaffUser
from backend.app.schemas.reservation import ReservationResponse, ReservationUpdate

router = APIRouter(prefix="/staff/reservations", tags=["Staff Reservations Management"])


@router.get("", response_model=List[ReservationResponse])
async def list_staff_reservations(
    branch_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_filter: Optional[str] = Query(None, alias="date"),
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List reservations, filterable by branch, status, and date."""
    stmt = (
        select(Reservation)
        .options(
            selectinload(Reservation.table),
            selectinload(Reservation.customer),
            selectinload(Reservation.branch),
        )
        .order_by(Reservation.start_time.asc())
    )

    if current_staff.branch_id:
        stmt = stmt.where(Reservation.branch_id == current_staff.branch_id)
    elif branch_id:
        stmt = stmt.where(Reservation.branch_id == branch_id)

    if status_filter:
        stmt = stmt.where(Reservation.status == status_filter)

    res = await db.execute(stmt)
    reservations = res.scalars().all()

    output = []
    for r in reservations:
        if date_filter and r.start_time.strftime("%Y-%m-%d") != date_filter:
            continue
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
                customer_name=r.customer.name if r.customer else None,
            )
        )
    return output


@router.patch("/{res_id}", response_model=ReservationResponse)
async def update_reservation(
    res_id: int,
    payload: ReservationUpdate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update reservation status, assign table, or add staff notes."""
    stmt = (
        select(Reservation)
        .where(Reservation.id == res_id)
        .options(
            selectinload(Reservation.table),
            selectinload(Reservation.customer),
            selectinload(Reservation.branch),
        )
    )
    res = await db.execute(stmt)
    reservation = res.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation #{res_id} not found.",
        )

    if current_staff.branch_id and reservation.branch_id != current_staff.branch_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage reservations for this branch.",
        )

    if payload.status:
        valid_statuses = ["pending", "confirmed", "seated", "completed", "cancelled"]
        if payload.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}.",
            )
        reservation.status = payload.status

    if payload.table_id is not None:
        reservation.table_id = payload.table_id

    if payload.notes is not None:
        reservation.notes = payload.notes

    await db.commit()
    await db.refresh(reservation)

    return ReservationResponse(
        id=reservation.id,
        customer_id=reservation.customer_id,
        branch_id=reservation.branch_id,
        table_id=reservation.table_id,
        party_size=reservation.party_size,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        duration_minutes=reservation.duration_minutes,
        seating_area_preference=reservation.seating_area_preference,
        status=reservation.status,
        notes=reservation.notes,
        created_at=reservation.created_at,
        table_label=reservation.table.label if reservation.table else None,
        branch_name=reservation.branch.name if reservation.branch else None,
        customer_name=reservation.customer.name if reservation.customer else None,
    )
