"""Tests for Auto-Confirm Reservations and PostgreSQL GIST Exclusion Double-Booking Guard."""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.app.agent.tools.table_tools import check_table_availability_and_book
from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Table
from backend.app.models.reservation import Reservation


@pytest.mark.asyncio
async def test_reservation_auto_confirmation():
    """Verify that requesting a free table automatically confirms without pending status."""
    # Book for tomorrow 7:00 PM
    tomorrow_evening = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=19, minute=0, second=0, microsecond=0
    )

    # Clean prior test reservation for this window if any
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(
            delete(Reservation).where(
                Reservation.branch_id == 1,
                Reservation.start_time >= tomorrow_evening - timedelta(hours=2),
                Reservation.start_time <= tomorrow_evening + timedelta(hours=2),
            )
        )
        await session.commit()

    result = await check_table_availability_and_book(
        customer_id=1,
        branch_id=1,
        start_time=tomorrow_evening,
        party_size=2,
        duration_minutes=90,
        seating_area="indoor",
    )

    assert result["success"] is True
    assert result["status"] == "confirmed"
    assert result["table_label"] is not None
    assert result["reservation_id"] is not None


@pytest.mark.asyncio
async def test_database_level_exclusion_constraint():
    """Verify that PostgreSQL EXCLUDE USING gist constraint prevents overlapping confirmed reservations

    on the same table even if direct insert bypasses application checks.
    """
    async with AsyncSessionLocal() as session:
        # Pick Table 1 at branch 1
        t_res = await session.execute(select(Table).where(Table.branch_id == 1))
        table = t_res.scalars().first()
        assert table is not None

    # Base time: 5 days from now 8:00 PM
    base_time = (datetime.now(timezone.utc) + timedelta(days=5)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )
    end_time = base_time + timedelta(minutes=90)

    # 1. Clean any existing reservations in this test window and insert first confirmed reservation
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(
            delete(Reservation).where(
                Reservation.table_id == table.id,
                Reservation.start_time < end_time,
                Reservation.end_time > base_time,
            )
        )
        await session.commit()

        res1 = Reservation(
            customer_id=1,
            branch_id=1,
            table_id=table.id,
            party_size=2,
            start_time=base_time,
            end_time=end_time,
            duration_minutes=90,
            status="confirmed",
            booking_window=func.tstzrange(base_time, end_time, "[)"),
        )
        session.add(res1)
        await session.commit()

    # 2. Attempt direct insert of overlapping reservation (starts 30 mins into the first window)
    overlapping_start = base_time + timedelta(minutes=30)
    overlapping_end = overlapping_start + timedelta(minutes=90)

    with pytest.raises(IntegrityError) as exc_info:
        async with AsyncSessionLocal() as session:
            res2 = Reservation(
                customer_id=1,
                branch_id=1,
                table_id=table.id,
                party_size=2,
                start_time=overlapping_start,
                end_time=overlapping_end,
                duration_minutes=90,
                status="confirmed",  # Confirmed status triggers exclusion constraint
                booking_window=func.tstzrange(overlapping_start, overlapping_end, "[)"),
            )
            session.add(res2)
            await session.commit()

    assert "no_overlapping_confirmed_table_reservations" in str(exc_info.value) or "exclusion" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_graceful_handling_when_table_taken():
    """Verify tool handles unavailable/conflicting table gracefully without throwing unhandled exceptions."""
    # Attempt booking when a conflicting table is already filled
    base_time = (datetime.now(timezone.utc) + timedelta(days=6)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )

    # Book all tables at branch 1 for that time
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        end_t = base_time + timedelta(minutes=90)
        await session.execute(
            delete(Reservation).where(
                Reservation.branch_id == 1,
                Reservation.start_time < end_t,
                Reservation.end_time > base_time,
            )
        )
        await session.commit()

        t_res = await session.execute(select(Table).where(Table.branch_id == 1, Table.seating_area == "rooftop"))
        rooftop_tables = t_res.scalars().all()
        for t in rooftop_tables:
            r = Reservation(
                customer_id=1,
                branch_id=1,
                table_id=t.id,
                party_size=4,
                start_time=base_time,
                end_time=end_t,
                duration_minutes=90,
                status="confirmed",
                booking_window=func.tstzrange(base_time, end_t, "[)"),
            )
            session.add(r)
        await session.commit()

    # Request rooftop table at that exact time
    result = await check_table_availability_and_book(
        customer_id=1,
        branch_id=1,
        start_time=base_time,
        party_size=4,
        duration_minutes=90,
        seating_area="rooftop",
    )

    assert result["success"] is False
    assert "No tables currently available" in result["error"]
    assert result.get("alternatives_available") is True
