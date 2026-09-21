"""Staff Authentication Routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.security import create_access_token, get_current_staff, get_password_hash, verify_password
from backend.app.database import get_db
from backend.app.models.user import StaffUser
from backend.app.schemas.auth import StaffLoginRequest, StaffResponse, TokenResponse

router = APIRouter(prefix="/staff", tags=["Staff Auth"])


@router.post("/login", response_model=TokenResponse)
async def staff_login(payload: StaffLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate staff member by username and password."""
    stmt = select(StaffUser).where(StaffUser.username == payload.username)
    res = await db.execute(stmt)
    staff = res.scalar_one_or_none()

    if not staff or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        data={
            "sub": str(staff.id),
            "type": "staff",
            "username": staff.username,
            "role": staff.role,
            "branch_id": staff.branch_id,
        }
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": staff.id,
            "username": staff.username,
            "role": staff.role,
            "branch_id": staff.branch_id,
            "type": "staff",
        },
    )


@router.get("/me", response_model=StaffResponse)
async def get_staff_me(current_staff: StaffUser = Depends(get_current_staff)):
    """Return currently logged-in staff profile."""
    return current_staff
