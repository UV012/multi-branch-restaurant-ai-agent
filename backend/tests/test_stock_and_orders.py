"""Tests for Inventory Stock Tracking and Atomic Order Placement."""

import asyncio
import pytest
from sqlalchemy import select, update

from backend.app.agent.tools.menu_tools import get_branch_menu_data
from backend.app.agent.tools.order_tools import create_order_atomic
from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Branch
from backend.app.models.menu import MenuItem, MenuItemStock


@pytest.mark.asyncio
async def test_order_rejection_when_exceeding_stock():
    """Verify that ordering more than available stock fails with an informative error."""
    async with AsyncSessionLocal() as session:
        # Find Truffle Mushroom Pizza at branch 1 (seeded with stock = 2)
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Truffle Mushroom Pizza", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        row = res.first()
        assert row is not None, "Seeded Truffle Mushroom Pizza should exist"
        stock_entry, menu_item = row

        # Set stock explicitly to 2 for deterministic test
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=2)
        )
        await session.commit()

    # Attempt to order 5 units when only 2 exist
    result = await create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 5}],
    )

    assert result["success"] is False
    assert "Insufficient stock" in result["error"]
    assert "Only 2 available" in result["error"]
    assert result.get("shortfall") == 3


@pytest.mark.asyncio
async def test_atomic_stock_decrement():
    """Verify stock decrements correctly and atomically on successful order."""
    async with AsyncSessionLocal() as session:
        # Find Margherita Pizza at branch 1
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Margherita Pizza", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        stock_entry, menu_item = res.first()

        # Set stock to 20
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=20)
        )
        await session.commit()

    # Order 3 pizzas
    result = await create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 3}],
    )

    assert result["success"] is True
    assert result["status"] == "placed"
    assert result["order_id"] is not None

    # Check updated stock in database
    async with AsyncSessionLocal() as session:
        check_res = await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )
        remaining_stock = check_res.scalar_one()
        assert remaining_stock == 17, f"Expected 17 remaining stock, got {remaining_stock}"


@pytest.mark.asyncio
async def test_concurrent_orders_for_last_unit():
    """Simulate two concurrent orders competing for 1 last available item.

    Exactly one must succeed, and the other must be rejected due to atomic DB locking.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Molten Chocolate Lava Cake", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        stock_entry, menu_item = res.first()

        # Set stock strictly to 1 unit
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=1)
        )
        await session.commit()

    # Launch two simultaneous order requests for the 1 unit
    task1 = create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 1}],
    )
    task2 = create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 1}],
    )

    results = await asyncio.gather(task1, task2)
    successes = [r for r in results if r.get("success") is True]
    failures = [r for r in results if r.get("success") is False]

    assert len(successes) == 1, "Exactly one order must succeed"
    assert len(failures) == 1, "The second concurrent order must fail"
    assert "stock" in failures[0]["error"].lower()

    # Verify final stock is 0
    async with AsyncSessionLocal() as session:
        check_res = await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )
        final_stock = check_res.scalar_one()
        assert final_stock == 0


@pytest.mark.asyncio
async def test_auto_unavailable_at_zero_stock():
    """Verify that when an item has 0 stock, effective_available is False in menu lookups."""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Molten Chocolate Lava Cake", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        stock_entry, menu_item = res.first()

        # Ensure stock is 0
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=0)
        )
        await session.commit()

    menu = await get_branch_menu_data(1)
    found_item = None
    for cat in menu["categories"]:
        for it in cat["items"]:
            if it["id"] == menu_item.id:
                found_item = it
                break

    assert found_item is not None
    assert found_item["stock_quantity"] == 0
    assert found_item["effective_available"] is False, "Item with 0 stock must be marked unavailable"


@pytest.mark.asyncio
async def test_order_cancel_and_uncancel_stock_reversal(async_client, staff_auth_headers):
    """Verify stock is restored upon cancellation and re-decremented upon un-cancellation."""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Margherita Pizza", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        stock_entry, menu_item = res.first()

        # Set stock explicitly to 10
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=10)
        )
        await session.commit()

    # 1. Place order for 2 pizzas -> stock should become 8
    order_res = await create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 2}],
    )
    assert order_res["success"] is True
    order_id = order_res["order_id"]

    async with AsyncSessionLocal() as session:
        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 8, "Stock should be 8 after placing order for 2 units"

    # 2. Cancel order -> assert stock restored to 10
    cancel_resp = await async_client.patch(
        f"/api/staff/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=staff_auth_headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    async with AsyncSessionLocal() as session:
        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 10, "Stock should be restored back to 10 after cancellation"

    # 3. Un-cancel back to placed -> assert stock re-decremented to 8
    uncancel_resp = await async_client.patch(
        f"/api/staff/orders/{order_id}/status",
        json={"status": "placed"},
        headers=staff_auth_headers,
    )
    assert uncancel_resp.status_code == 200
    assert uncancel_resp.json()["status"] == "placed"

    async with AsyncSessionLocal() as session:
        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 8, "Stock should be re-decremented to 8 after un-cancellation"


@pytest.mark.asyncio
async def test_uncancel_conflict_when_stock_insufficient(async_client, staff_auth_headers):
    """Place order A (takes last unit) -> cancel A (stock restored) -> order B (consumes restored stock)

    -> attempt un-cancel A -> assert 409 conflict, A stays cancelled, B's stock untouched.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(MenuItemStock, MenuItem)
            .join(MenuItem, MenuItemStock.menu_item_id == MenuItem.id)
            .where(MenuItem.name == "Truffle Mushroom Pizza", MenuItemStock.branch_id == 1)
        )
        res = await session.execute(stmt)
        stock_entry, menu_item = res.first()

        # Set stock explicitly to 1
        await session.execute(
            update(MenuItemStock)
            .where(MenuItemStock.id == stock_entry.id)
            .values(stock_quantity=1)
        )
        await session.commit()

    # 1. Place Order A for 1 unit (the last unit)
    order_a_res = await create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 1}],
    )
    assert order_a_res["success"] is True
    order_a_id = order_a_res["order_id"]

    # 2. Cancel Order A (stock restored to 1)
    cancel_a_resp = await async_client.patch(
        f"/api/staff/orders/{order_a_id}/status",
        json={"status": "cancelled"},
        headers=staff_auth_headers,
    )
    assert cancel_a_resp.status_code == 200

    async with AsyncSessionLocal() as session:
        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 1, "Stock should be restored to 1 after cancelling Order A"

    # 3. Place Order B consuming that same restored stock
    order_b_res = await create_order_atomic(
        customer_id=1,
        branch_id=1,
        order_type="dine_in",
        items=[{"menu_item_id": menu_item.id, "quantity": 1}],
    )
    assert order_b_res["success"] is True
    order_b_id = order_b_res["order_id"]

    async with AsyncSessionLocal() as session:
        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 0, "Stock should be 0 after Order B consumed the unit"

    # 4. Attempt to un-cancel Order A back to placed -> assert 409 Conflict
    uncancel_a_resp = await async_client.patch(
        f"/api/staff/orders/{order_a_id}/status",
        json={"status": "placed"},
        headers=staff_auth_headers,
    )
    assert uncancel_a_resp.status_code == 409
    assert menu_item.name in uncancel_a_resp.json()["detail"]

    # 5. Assert Order A stays cancelled and Order B's stock is untouched
    async with AsyncSessionLocal() as session:
        from backend.app.models.order import Order
        order_a_db = (await session.execute(
            select(Order).where(Order.id == order_a_id)
        )).scalar_one()
        assert order_a_db.status == "cancelled", "Order A must stay cancelled"

        order_b_db = (await session.execute(
            select(Order).where(Order.id == order_b_id)
        )).scalar_one()
        assert order_b_db.status == "placed", "Order B must stay placed"

        stock_val = (await session.execute(
            select(MenuItemStock.stock_quantity).where(MenuItemStock.id == stock_entry.id)
        )).scalar_one()
        assert stock_val == 0, "Stock must remain 0"

    # 6. Idempotent no-op test: updating Order A with status "cancelled" again is an idempotent no-op
    noop_resp = await async_client.patch(
        f"/api/staff/orders/{order_a_id}/status",
        json={"status": "cancelled"},
        headers=staff_auth_headers,
    )
    assert noop_resp.status_code == 200
