"""Table Availability and Auto-Confirm Reservation Tools."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Branch, Table
from backend.app.models.reservation import Reservation


async def check_table_availability_and_book(
    customer_id: int,
    branch_id: int,
    start_time: datetime,
    party_size: int,
    duration_minutes: int = 90,
    seating_area: Optional[str] = "indoor",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Find an eligible table and auto-confirm reservation, guarded by DB-level exclusion constraint.

    Args:
        customer_id: Authenticated customer id.
        branch_id: Chosen branch id.
        start_time: Requested start datetime (timezone-aware).
        party_size: Number of guests.
        duration_minutes: Duration of dining slot (default 90 mins).
        seating_area: "indoor", "outdoor", "rooftop", or "any".
        notes: Special customer notes.

    Returns:
        Dict indicating success/failure, reservation details, or alternative suggestions.
    """
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(minutes=duration_minutes)

    async with AsyncSessionLocal() as session:
        # Verify branch
        branch_res = await session.execute(
            select(Branch).where(Branch.id == branch_id, Branch.is_active == True)
        )
        branch = branch_res.scalar_one_or_none()
        if not branch:
            return {"success": False, "error": f"Branch #{branch_id} not found."}

        # 1. Query candidate tables matching capacity and area
        base_query = (
            select(Table)
            .where(
                Table.branch_id == branch_id,
                Table.is_available == True,
                Table.capacity >= party_size,
            )
            .order_by(Table.capacity.asc())  # Best fit capacity first
        )

        area_filter = seating_area.lower() if seating_area else "any"
        if area_filter != "any":
            table_query = base_query.where(Table.seating_area == area_filter)
        else:
            table_query = base_query

        table_res = await session.execute(table_query)
        candidate_tables = table_res.scalars().all()

        # Find which of these candidate tables are free of overlapping confirmed reservations
        chosen_table = None
        for table in candidate_tables:
            conflict_stmt = select(Reservation).where(
                Reservation.table_id == table.id,
                Reservation.status == "confirmed",
                # Overlap check: existing_start < new_end AND existing_end > new_start
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            )
            conflict_res = await session.execute(conflict_stmt)
            if not conflict_res.scalar_one_or_none():
                chosen_table = table
                break

        # 2. If no table in preferred area, search other areas or alternative times
        if not chosen_table:
            alt_areas = []
            if area_filter != "any":
                # Check if other areas have tables free right now
                alt_table_res = await session.execute(base_query)
                other_tables = alt_table_res.scalars().all()
                for table in other_tables:
                    conflict_stmt = select(Reservation).where(
                        Reservation.table_id == table.id,
                        Reservation.status == "confirmed",
                        Reservation.start_time < end_time,
                        Reservation.end_time > start_time,
                    )
                    c_res = await session.execute(conflict_stmt)
                    if not c_res.scalar_one_or_none():
                        alt_areas.append(f"{table.seating_area.capitalize()} (Table {table.label})")

            alternatives_msg = ""
            if alt_areas:
                alternatives_msg = f" However, we have availability in our {', '.join(set(alt_areas))} area(s)."
            else:
                alternatives_msg = " We also have availability earlier or later in the evening."

            return {
                "success": False,
                "error": f"No tables currently available for {party_size} guests in the {area_filter} area at {start_time.strftime('%I:%M %p')}.{alternatives_msg}",
                "alternatives_available": True,
            }

        # 3. Insert confirmed reservation guarded by PostgreSQL EXCLUDE USING gist constraint
        try:
            new_res = Reservation(
                customer_id=customer_id,
                branch_id=branch_id,
                table_id=chosen_table.id,
                party_size=party_size,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                seating_area_preference=chosen_table.seating_area,
                status="confirmed",  # Auto-confirm!
                notes=notes,
                booking_window=func.tstzrange(start_time, end_time, "[)"),
            )
            session.add(new_res)
            await session.commit()
            await session.refresh(new_res)

            return {
                "success": True,
                "reservation_id": new_res.id,
                "status": "confirmed",
                "branch_name": branch.name,
                "table_label": chosen_table.label,
                "seating_area": chosen_table.seating_area,
                "date": start_time.strftime("%Y-%m-%d"),
                "time": start_time.strftime("%I:%M %p"),
                "party_size": party_size,
                "duration_minutes": duration_minutes,
            }

        except IntegrityError as exc:
            # Caught race-condition / DB-level exclusion constraint violation!
            await session.rollback()
            return {
                "success": False,
                "error": "That table was just reserved moments ago by another guest. Please choose an alternative time slot or seating area.",
                "race_conflict": True,
            }
