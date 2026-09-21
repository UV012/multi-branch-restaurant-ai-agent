"""Test Checkpointer Pool Lifecycle and Chat Endpoint Concurrency without PoolTimeout."""

import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.auth.security import create_access_token
from backend.app.main import app, lifespan


@pytest.mark.asyncio
async def test_chat_pool_lifecycle_and_rapid_requests():
    """Verify checkpointer pool lifecycle in lifespan and execute 5+ consecutive chat requests with zero delay."""
    # Test lifespan startup and shutdown
    async with lifespan(app):
        assert hasattr(app.state, "checkpointer_pool"), "Lifespan must set app.state.checkpointer_pool"
        assert hasattr(app.state, "checkpointer"), "Lifespan must set app.state.checkpointer"
        assert not app.state.checkpointer_pool.closed, "Checkpointer pool should be open and active"

        # Customer token
        token = create_access_token({"sub": "1", "type": "customer", "email": "customer@example.com"})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Send 6 rapid requests in a row with zero delay
            for i in range(6):
                resp = await client.post(
                    "/api/chat",
                    headers=headers,
                    json={"message": f"Hello branch check {i}"},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "reply" in data
                assert "couldn't get a connection after" not in data["reply"]
                assert "PoolTimeout" not in data["reply"]

    # Verify pool closed cleanly on lifespan exit
    assert app.state.checkpointer_pool.closed, "Checkpointer pool must be closed after lifespan exit"


@pytest.mark.asyncio
async def test_backend_restart_first_request_no_timeout():
    """Verify restarting backend creates a ready pool and the very first chat request succeeds immediately."""
    async with lifespan(app):
        token = create_access_token({"sub": "1", "type": "customer", "email": "customer@example.com"})
        headers = {"Authorization": f"Bearer {token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request right after startup
            resp = await client.post(
                "/api/chat",
                headers=headers,
                json={"message": "Hi, which branches do you have?"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "couldn't get a connection" not in data["reply"]
            assert "PoolTimeout" not in data["reply"]
