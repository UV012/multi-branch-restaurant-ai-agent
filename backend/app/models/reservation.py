"""Reservation Model with PostgreSQL Exclusion Constraint Guard."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint, TSTZRANGE
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    table_id = Column(Integer, ForeignKey("tables.id", ondelete="CASCADE"), nullable=True, index=True)

    party_size = Column(Integer, nullable=False, default=2)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=90)
    seating_area_preference = Column(String(50), nullable=True, default="indoor")  # indoor, outdoor, rooftop, any

    # Status: confirmed (default auto-confirm via agent), pending, seated, completed, cancelled
    status = Column(String(50), nullable=False, default="confirmed", index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # PostgreSQL TSTZRANGE for exclusion constraint
    booking_window = Column(TSTZRANGE, nullable=False)

    __table_args__ = (
        # Exclude concurrent overlapping confirmed reservations on the same table
        ExcludeConstraint(
            ("table_id", "="),
            ("booking_window", "&&"),
            where=text("status = 'confirmed'"),
            name="no_overlapping_confirmed_table_reservations",
            using="gist",
        ),
    )

    # Relationships
    customer = relationship("Customer", back_populates="reservations")
    branch = relationship("Branch", back_populates="reservations")
    table = relationship("Table", back_populates="reservations")

    @classmethod
    def calculate_window(cls, start: datetime, duration_minutes: int = 90):
        """Calculate start, end, and postgres range representation."""
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        end = start + timedelta(minutes=duration_minutes)
        return start, end
