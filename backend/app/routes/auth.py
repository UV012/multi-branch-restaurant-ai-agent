"""Customer Authentication Routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.security import create_access_token, get_current_customer, get_password_hash, verify_password
from backend.app.database import get_db
from backend.app.models.user import Customer
from backend.app.schemas.auth import (
    CustomerLoginRequest,
    CustomerRegisterRequest,
    CustomerResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Customer Auth"])


@router.post("/register", response_model=TokenResponse)
async def register_customer(payload: CustomerRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new customer account."""
    # Check if email exists
    existing = await db.execute(select(Customer).where(Customer.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    new_customer = Customer(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        phone=payload.phone,
    )
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    token = create_access_token(data={"sub": str(new_customer.id), "type": "customer", "email": new_customer.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": new_customer.id,
            "name": new_customer.name,
            "email": new_customer.email,
            "phone": new_customer.phone,
            "type": "customer",
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login_customer(payload: CustomerLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login customer with email and password."""
    stmt = select(Customer).where(Customer.email == payload.email)
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()

    if not customer or not verify_password(payload.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(data={"sub": str(customer.id), "type": "customer", "email": customer.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "type": "customer",
        },
    )


@router.get("/me", response_model=CustomerResponse)
async def get_me(current_user: Customer = Depends(get_current_customer)):
    """Return currently logged-in customer profile."""
    return current_user
