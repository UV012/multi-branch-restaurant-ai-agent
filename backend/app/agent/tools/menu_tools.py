"""Menu and Inventory Agent Tools."""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Branch
from backend.app.models.menu import MenuCategory, MenuItem, MenuItemStock


async def get_branch_menu_data(branch_id: int) -> Dict[str, Any]:
    """Retrieve full active menu for a branch, including stock levels and variant options."""
    async with AsyncSessionLocal() as session:
        # Check branch
        branch_stmt = select(Branch).where(Branch.id == branch_id, Branch.is_active == True)
        branch_res = await session.execute(branch_stmt)
        branch = branch_res.scalar_one_or_none()
        if not branch:
            return {"error": f"Branch #{branch_id} not found or inactive."}

        # Categories with items and variants
        cat_stmt = (
            select(MenuCategory)
            .where(MenuCategory.branch_id == branch_id)
            .options(
                selectinload(MenuCategory.items).selectinload(MenuItem.variants),
            )
        )
        cat_res = await session.execute(cat_stmt)
        categories = cat_res.scalars().all()

        # Fetch stocks for this branch
        stock_stmt = select(MenuItemStock).where(MenuItemStock.branch_id == branch_id)
        stock_res = await session.execute(stock_stmt)
        stocks_map = {s.menu_item_id: s.stock_quantity for s in stock_res.scalars().all()}

        menu_data = {
            "branch_id": branch.id,
            "branch_name": branch.name,
            "categories": [],
        }

        for cat in categories:
            cat_dict = {"id": cat.id, "name": cat.name, "items": []}
            for item in cat.items:
                stock_qty = stocks_map.get(item.id, 0)
                # Auto-unavailable if stock reaches 0 or staff manually disabled
                effective_available = item.is_available and (stock_qty > 0)

                cat_dict["items"].append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "base_price": item.base_price,
                        "is_available": item.is_available,
                        "stock_quantity": stock_qty,
                        "effective_available": effective_available,
                        "variants": [
                            {
                                "id": v.id,
                                "type": v.variant_type,
                                "name": v.variant_name,
                                "price_delta": v.price_delta,
                            }
                            for v in item.variants
                        ],
                    }
                )
            menu_data["categories"].append(cat_dict)

        return menu_data


async def format_menu_for_prompt(branch_id: int) -> str:
    """Format the branch menu into a clean text summary for LLM context."""
    data = await get_branch_menu_data(branch_id)
    if "error" in data:
        return data["error"]

    lines = [f"--- Menu for {data['branch_name']} ---"]
    for cat in data["categories"]:
        lines.append(f"\n[{cat['name']}]")
        for item in cat["items"]:
            if not item["effective_available"]:
                lines.append(f"  • {item['name']} - [OUT OF STOCK / UNAVAILABLE]")
                continue

            variant_desc = []
            for v in item["variants"]:
                delta_str = f" (+${v['price_delta']:.2f})" if v["price_delta"] > 0 else (f" (-${abs(v['price_delta']):.2f})" if v["price_delta"] < 0 else "")
                variant_desc.append(f"{v['name']}{delta_str}")

            var_info = f" (Options: {', '.join(variant_desc)})" if variant_desc else ""
            stock_info = f" [Stock: {item['stock_quantity']}]"
            lines.append(f"  • #{item['id']} {item['name']} - ${item['base_price']:.2f}{var_info}{stock_info}")
            if item["description"]:
                lines.append(f"    {item['description']}")

    return "\n".join(lines)
