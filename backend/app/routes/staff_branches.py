"""Staff Branch and Table Management Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.security import get_current_staff, require_admin
from backend.app.database import get_db
from backend.app.models.branch import Branch, Table
from backend.app.models.user import StaffUser
from backend.app.schemas.branch import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    TableCreate,
    TableResponse,
    TableUpdate,
)

router = APIRouter(prefix="/staff/branches", tags=["Staff Branches & Tables"])


@router.get("", response_model=List[BranchResponse])
async def list_branches(
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List branches with their tables."""
    stmt = select(Branch).options(selectinload(Branch.tables)).order_by(Branch.id.asc())
    if current_staff.branch_id:
        stmt = stmt.where(Branch.id == current_staff.branch_id)

    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=BranchResponse)
async def create_branch(
    payload: BranchCreate,
    current_admin: StaffUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new restaurant branch (Admin only)."""
    branch = Branch(**payload.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    current_admin: StaffUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update branch details (Admin only)."""
    res = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = res.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(branch, k, v)

    await db.commit()
    await db.refresh(branch)
    return branch


# Table Management
@router.get("/tables", response_model=List[TableResponse])
async def list_tables(
    branch_id: Optional[int] = Query(None),
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List tables for a branch."""
    b_id = current_staff.branch_id or branch_id or 1
    stmt = select(Table).where(Table.branch_id == b_id).order_by(Table.label.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/tables", response_model=TableResponse)
async def create_table(
    payload: TableCreate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Add a new table to a branch."""
    if current_staff.branch_id and payload.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    table = Table(**payload.model_dump())
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.patch("/tables/{table_id}", response_model=TableResponse)
async def update_table(
    table_id: int,
    payload: TableUpdate,
    current_staff: StaffUser = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update table label, seating area, capacity, or availability."""
    res = await db.execute(select(Table).where(Table.id == table_id))
    table = res.scalar_one_or_none()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found.")

    if current_staff.branch_id and table.branch_id != current_staff.branch_id:
        raise HTTPException(status_code=403, detail="Permission denied for this branch.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(table, k, v)

    await db.commit()
    await db.refresh(table)
    return table
