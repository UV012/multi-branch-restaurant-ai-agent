"""Reservation Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReservationCreate(BaseModel):
    branch_id: int
    party_size: int = 2
    requested_date: str  # YYYY-MM-DD
    requested_time: str  # HH:MM (24-hour)
    duration_minutes: int = 90
    seating_area_preference: Optional[str] = "indoor"  # indoor, outdoor, rooftop, any
    notes: Optional[str] = None


class ReservationUpdate(BaseModel):
    status: Optional[str] = None  # pending, confirmed, seated, completed, cancelled
    table_id: Optional[int] = None
    notes: Optional[str] = None


class ReservationResponse(BaseModel):
    id: int
    customer_id: int
    branch_id: int
    table_id: Optional[int] = None
    party_size: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    seating_area_preference: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    table_label: Optional[str] = None
    branch_name: Optional[str] = None
    customer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
