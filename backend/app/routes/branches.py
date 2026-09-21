"""Public Branch and Menu Explorer Endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.agent.tools.faq_tools import get_branch_faq
from backend.app.agent.tools.menu_tools import get_branch_menu_data
from backend.app.database import get_db
from backend.app.models.branch import Branch
from backend.app.schemas.branch import BranchResponse

router = APIRouter(prefix="/branches", tags=["Branches & Menus"])


@router.get("", response_model=List[BranchResponse])
async def list_active_branches(db: AsyncSession = Depends(get_db)):
    """List all active restaurant branches."""
    stmt = (
        select(Branch)
        .where(Branch.is_active == True)
        .options(selectinload(Branch.tables))
        .order_by(Branch.id.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{branch_id}/menu")
async def get_branch_menu(branch_id: int):
    """Retrieve full menu for a branch including real-time stock and availability."""
    data = await get_branch_menu_data(branch_id)
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=data["error"],
        )
    return data


@router.get("/{branch_id}/faq")
async def get_branch_info(branch_id: int):
    """Retrieve opening hours, address, contact, and dining policies for a branch."""
    faq = await get_branch_faq(branch_id)
    if "error" in faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=faq["error"],
        )
    return faq
