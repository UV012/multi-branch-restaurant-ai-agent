"""Branch FAQ and Information Lookup Tools."""

from typing import Any, Dict
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.branch import Branch


async def get_branch_faq(branch_id: int) -> Dict[str, Any]:
    """Retrieve opening hours, address, contact, and dining policies for a branch."""
    async with AsyncSessionLocal() as session:
        branch_stmt = select(Branch).where(Branch.id == branch_id)
        branch_res = await session.execute(branch_stmt)
        branch = branch_res.scalar_one_or_none()
        if not branch:
            return {"error": f"Branch #{branch_id} not found."}

        # Per-branch FAQ policies (lookup table)
        policies = {
            1: {
                "parking": "Valet parking available at the front entrance; street parking available on Main St.",
                "dress_code": "Smart casual. No beachwear.",
                "cancellation_policy": "Reservations can be modified or cancelled up to 1 hour before dining.",
                "payment_methods": "Cash, credit/debit cards accepted at the counter or upon delivery.",
                "delivery_radius": "Delivers within 7 miles of Downtown Central City.",
            },
            2: {
                "parking": "Dedicated customer parking lot behind the building.",
                "dress_code": "Casual to elegant.",
                "cancellation_policy": "Reservations can be modified or cancelled up to 1 hour before dining.",
                "payment_methods": "Cash, credit/debit cards accepted at the counter or upon delivery.",
                "delivery_radius": "Delivers within 10 miles of North Hills.",
            },
        }

        branch_policy = policies.get(
            branch.id,
            {
                "parking": "Street parking available nearby.",
                "dress_code": "Casual.",
                "cancellation_policy": "Free cancellation up to 1 hour prior.",
                "payment_methods": "Cash or card at counter/delivery.",
                "delivery_radius": "Standard city delivery radius.",
            },
        )

        return {
            "branch_id": branch.id,
            "branch_name": branch.name,
            "address": branch.address,
            "phone": branch.phone,
            "opening_hours": branch.opening_hours,
            "policies": branch_policy,
        }
