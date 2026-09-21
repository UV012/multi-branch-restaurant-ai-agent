"""Branch and Table Schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TableBase(BaseModel):
    label: str
    seating_area: str  # indoor, outdoor, rooftop
    capacity: int = 2
    is_available: bool = True


class TableCreate(TableBase):
    branch_id: int


class TableUpdate(BaseModel):
    label: Optional[str] = None
    seating_area: Optional[str] = None
    capacity: Optional[int] = None
    is_available: Optional[bool] = None


class TableResponse(TableBase):
    id: int
    branch_id: int

    model_config = ConfigDict(from_attributes=True)


class BranchBase(BaseModel):
    name: str
    address: str
    phone: str
    opening_hours: str = "10:00 AM - 10:00 PM"
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    tables: List[TableResponse] = []

    model_config = ConfigDict(from_attributes=True)
