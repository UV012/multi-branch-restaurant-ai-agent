"""Unit and Integration Tests for Customer and Staff Authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_register_and_login(async_client: AsyncClient):
    """Test customer registration and login flows."""
    email = f"testuser_{pytest.test_id if hasattr(pytest, 'test_id') else 'flow'}@example.com"
    reg_payload = {
        "name": "Bob Tester",
        "email": email,
        "password": "SecretPassword123",
        "phone": "+1-555-8888",
    }

    # Register
    reg_resp = await async_client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code in [200, 400]
    if reg_resp.status_code == 200:
        data = reg_resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == email

    # Login
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "SecretPassword123"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # Profile with Bearer token
    me_resp = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["name"] == "Bob Tester"


@pytest.mark.asyncio
async def test_staff_login(async_client: AsyncClient):
    """Test seeded admin login."""
    resp = await async_client.post(
        "/api/staff/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "admin"
    token = data["access_token"]

    # Verify staff profile
    me_resp = await async_client.get(
        "/api/staff/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """Verify endpoints block unauthenticated requests."""
    orders_resp = await async_client.get("/api/orders/me")
    assert orders_resp.status_code == 401

    staff_orders = await async_client.get("/api/staff/orders")
    assert staff_orders.status_code == 401
