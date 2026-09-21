"""Order Placement and Atomic Stock Management Tools."""

from typing import Any, Dict, List, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import AsyncSessionLocal
from backend.app.models.menu import MenuItem, MenuItemStock, MenuItemVariant
from backend.app.models.order import Order, OrderItem


async def create_order_atomic(
    customer_id: int,
    branch_id: int,
    order_type: str,
    items: List[Dict[str, Any]],
    delivery_address: str = None,
    special_notes: str = None,
) -> Dict[str, Any]:
    """Atomically validate stock, decrement inventory, and insert Order + OrderItems.

    Args:
        customer_id: Customer ID placing the order.
        branch_id: Branch ID from which the order is placed.
        order_type: "dine_in", "takeaway", or "delivery".
        items: List of dicts, each with:
            - menu_item_id: int
            - quantity: int
            - selected_variants: Optional[List[Dict[str, Any]]] (e.g. [{"name": "Large", "delta": 4.0}])
            - item_notes: Optional[str]
        delivery_address: Required if order_type == 'delivery'.
        special_notes: Optional special instructions.

    Returns:
        Dict with success status, order_id, total_amount, or detailed error message.
    """
    if not items:
        return {"success": False, "error": "Order cannot be empty. Please specify items to order."}

    if order_type == "delivery" and not delivery_address:
        return {"success": False, "error": "Delivery orders require a delivery address. Please provide your address."}

    async with AsyncSessionLocal() as session:
        async with session.begin():
            total_order_amount = 0.0
            processed_order_items = []

            # 1. Pre-validation: Check all items, variants, and current stock
            for req_item in items:
                item_id = req_item.get("menu_item_id")
                qty = req_item.get("quantity", 1)
                if qty <= 0:
                    return {"success": False, "error": f"Quantity for item #{item_id} must be at least 1."}

                # Query menu item
                item_stmt = select(MenuItem).where(MenuItem.id == item_id)
                item_res = await session.execute(item_stmt)
                menu_item = item_res.scalar_one_or_none()
                if not menu_item:
                    return {"success": False, "error": f"Item #{item_id} does not exist."}
                if not menu_item.is_available:
                    return {"success": False, "error": f"'{menu_item.name}' is currently unavailable."}

                # Check stock quantity at this specific branch using SELECT ... FOR UPDATE (row lock)
                stock_stmt = (
                    select(MenuItemStock)
                    .where(
                        MenuItemStock.menu_item_id == item_id,
                        MenuItemStock.branch_id == branch_id,
                    )
                    .with_for_update()
                )
                stock_res = await session.execute(stock_stmt)
                stock_entry = stock_res.scalar_one_or_none()

                available_qty = stock_entry.stock_quantity if stock_entry else 0
                if available_qty < qty:
                    shortfall = qty - available_qty
                    if available_qty == 0:
                        return {
                            "success": False,
                            "error": f"'{menu_item.name}' is currently out of stock at this branch.",
                            "out_of_stock_item": menu_item.name,
                            "available_quantity": 0,
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Insufficient stock for '{menu_item.name}'. Only {available_qty} available (requested {qty}, short by {shortfall}). Please adjust your quantity.",
                            "shortfall_item": menu_item.name,
                            "available_quantity": available_qty,
                            "shortfall": shortfall,
                        }

                # Calculate item price with variants
                unit_price = float(menu_item.base_price)
                selected_variants = req_item.get("selected_variants", []) or []
                for v in selected_variants:
                    delta = float(v.get("delta") or v.get("price_delta") or 0.0)
                    unit_price += delta

                item_total = unit_price * qty
                total_order_amount += item_total

                # 2. Atomic conditional decrement of stock:
                # UPDATE menu_item_stocks SET stock_quantity = stock_quantity - :qty
                # WHERE menu_item_id = :id AND branch_id = :b_id AND stock_quantity >= :qty
                decrement_stmt = (
                    update(MenuItemStock)
                    .where(
                        MenuItemStock.menu_item_id == item_id,
                        MenuItemStock.branch_id == branch_id,
                        MenuItemStock.stock_quantity >= qty,
                    )
                    .values(stock_quantity=MenuItemStock.stock_quantity - qty)
                )
                update_result = await session.execute(decrement_stmt)
                if update_result.rowcount != 1:
                    # Stock changed concurrently or was insufficient
                    return {
                        "success": False,
                        "error": f"Stock condition changed for '{menu_item.name}'. Please retry.",
                    }

                processed_order_items.append(
                    {
                        "menu_item_id": item_id,
                        "menu_item_name": menu_item.name,
                        "quantity": qty,
                        "unit_price": unit_price,
                        "selected_variants": selected_variants,
                        "item_notes": req_item.get("item_notes"),
                    }
                )

            # 3. Insert Order
            new_order = Order(
                customer_id=customer_id,
                branch_id=branch_id,
                order_type=order_type,
                status="placed",
                delivery_address=delivery_address if order_type == "delivery" else None,
                special_notes=special_notes,
                total_amount=round(total_order_amount, 2),
            )
            session.add(new_order)
            await session.flush()

            # 4. Insert Order Items
            for p_item in processed_order_items:
                oi = OrderItem(
                    order_id=new_order.id,
                    menu_item_id=p_item["menu_item_id"],
                    quantity=p_item["quantity"],
                    unit_price=p_item["unit_price"],
                    selected_variants=p_item["selected_variants"],
                    item_notes=p_item["item_notes"],
                )
                session.add(oi)

            # Commit transaction atomically
            await session.commit()

            return {
                "success": True,
                "order_id": new_order.id,
                "status": "placed",
                "total_amount": round(total_order_amount, 2),
                "order_type": order_type,
                "items": processed_order_items,
            }
