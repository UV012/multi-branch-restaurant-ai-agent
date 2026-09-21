"""Pytest Configuration and Fixtures."""

import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.auth.security import create_access_token, get_password_hash
from backend.app.database import AsyncSessionLocal, engine, init_db
from backend.app.main import app
from backend.app.models.branch import Branch, Table
from backend.app.models.menu import MenuCategory, MenuItem, MenuItemStock, MenuItemVariant
from backend.app.models.user import Customer, StaffUser


@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    """Ensure database tables and btree_gist extension are initialized and pool disposed."""
    await init_db()
    yield
    await engine.dispose()


@pytest.fixture
async def async_client():
    """Provide AsyncClient for FastAPI test requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def customer_auth_headers():
    """Generate headers for a valid test customer."""
    token = create_access_token({"sub": "1", "type": "customer", "email": "customer@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_auth_headers():
    """Generate headers for a valid test staff admin."""
    token = create_access_token({"sub": "1", "type": "staff", "username": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}
