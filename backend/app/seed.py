"""Database Seeder Script."""

import asyncio
from sqlalchemy import select
from backend.app.auth.security import get_password_hash
from backend.app.database import AsyncSessionLocal, init_db
from backend.app.models.branch import Branch, Table
from backend.app.models.menu import MenuCategory, MenuItem, MenuItemStock, MenuItemVariant
from backend.app.models.user import Customer, StaffUser


async def seed_data() -> None:
    """Populate database with sample branches, tables, menus, variants, inventory, and users."""
    print("Ensuring tables and extensions are created...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Branch))
        existing_branch = result.scalar_one_or_none()
        if existing_branch:
            print("Database already contains branch data. Skipping duplicate seed.")
            return

        print("Seeding Branches...")
        b1 = Branch(
            name="Downtown Bistro",
            address="123 Main St, Central City",
            phone="+1-555-0100",
            opening_hours="10:00 AM - 10:00 PM",
            is_active=True,
        )
        b2 = Branch(
            name="Uptown Terrace",
            address="456 High St, North Hills",
            phone="+1-555-0200",
            opening_hours="11:00 AM - 11:00 PM",
            is_active=True,
        )
        session.add_all([b1, b2])
        await session.flush()

        print("Seeding Tables...")
        tables = [
            # Downtown Bistro Tables
            Table(branch_id=b1.id, label="T1 (Indoor)", seating_area="indoor", capacity=2, is_available=True),
            Table(branch_id=b1.id, label="T2 (Indoor)", seating_area="indoor", capacity=4, is_available=True),
            Table(branch_id=b1.id, label="T3 (Indoor)", seating_area="indoor", capacity=6, is_available=True),
            Table(branch_id=b1.id, label="P1 (Patio)", seating_area="outdoor", capacity=2, is_available=True),
            Table(branch_id=b1.id, label="P2 (Patio)", seating_area="outdoor", capacity=4, is_available=True),
            Table(branch_id=b1.id, label="R1 (Roof)", seating_area="rooftop", capacity=4, is_available=True),
            # Uptown Terrace Tables
            Table(branch_id=b2.id, label="U1 (Indoor)", seating_area="indoor", capacity=2, is_available=True),
            Table(branch_id=b2.id, label="U2 (Indoor)", seating_area="indoor", capacity=4, is_available=True),
            Table(branch_id=b2.id, label="O1 (Garden)", seating_area="outdoor", capacity=4, is_available=True),
            Table(branch_id=b2.id, label="R1 (Terrace)", seating_area="rooftop", capacity=6, is_available=True),
            Table(branch_id=b2.id, label="R2 (Terrace)", seating_area="rooftop", capacity=8, is_available=True),
        ]
        session.add_all(tables)
        await session.flush()

        print("Seeding Menu Categories...")
        cat_b1_pizza = MenuCategory(branch_id=b1.id, name="Pizzas")
        cat_b1_pasta = MenuCategory(branch_id=b1.id, name="Pastas")
        cat_b1_drinks = MenuCategory(branch_id=b1.id, name="Beverages")
        cat_b1_desserts = MenuCategory(branch_id=b1.id, name="Desserts")

        cat_b2_pizza = MenuCategory(branch_id=b2.id, name="Artisan Pizzas")
        cat_b2_drinks = MenuCategory(branch_id=b2.id, name="Specialty Drinks")

        session.add_all([cat_b1_pizza, cat_b1_pasta, cat_b1_drinks, cat_b1_desserts, cat_b2_pizza, cat_b2_drinks])
        await session.flush()

        print("Seeding Menu Items, Variants, and Stocks...")
        # Items for Downtown Bistro
        # 1. Margherita Pizza
        item_margherita = MenuItem(
            category_id=cat_b1_pizza.id,
            name="Margherita Pizza",
            description="Classic sourdough pizza with San Marzano tomatoes, fresh mozzarella, and aromatic basil.",
            base_price=12.00,
            is_available=True,
        )
        session.add(item_margherita)
        await session.flush()

        variants_margherita = [
            MenuItemVariant(menu_item_id=item_margherita.id, variant_type="size", variant_name="Small (10\")", price_delta=-2.00),
            MenuItemVariant(menu_item_id=item_margherita.id, variant_type="size", variant_name="Medium (12\")", price_delta=0.00),
            MenuItemVariant(menu_item_id=item_margherita.id, variant_type="size", variant_name="Large (14\")", price_delta=4.00),
            MenuItemVariant(menu_item_id=item_margherita.id, variant_type="topping", variant_name="Extra Mozzarella", price_delta=2.00),
            MenuItemVariant(menu_item_id=item_margherita.id, variant_type="topping", variant_name="Kalamata Olives", price_delta=1.50),
        ]
        stock_margherita = MenuItemStock(menu_item_id=item_margherita.id, branch_id=b1.id, stock_quantity=40)
        session.add_all(variants_margherita + [stock_margherita])

        # 2. Truffle Mushroom Pizza (LOW STOCK = 2 to exercise low-stock/out-of-stock flows)
        item_truffle = MenuItem(
            category_id=cat_b1_pizza.id,
            name="Truffle Mushroom Pizza",
            description="Wild forest mushrooms, white truffle oil, shaved pecorino, and creamy garlic base.",
            base_price=16.50,
            is_available=True,
        )
        session.add(item_truffle)
        await session.flush()
        variants_truffle = [
            MenuItemVariant(menu_item_id=item_truffle.id, variant_type="size", variant_name="Medium", price_delta=0.00),
            MenuItemVariant(menu_item_id=item_truffle.id, variant_type="size", variant_name="Large", price_delta=4.50),
        ]
        stock_truffle = MenuItemStock(menu_item_id=item_truffle.id, branch_id=b1.id, stock_quantity=2)
        session.add_all(variants_truffle + [stock_truffle])

        # 3. Pepperoni Feast
        item_pepperoni = MenuItem(
            category_id=cat_b1_pizza.id,
            name="Pepperoni Feast Pizza",
            description="Loaded with crispy artisanal pepperoni, crushed chili flakes, and double mozzarella.",
            base_price=14.50,
            is_available=True,
        )
        session.add(item_pepperoni)
        await session.flush()
        stock_pepperoni = MenuItemStock(menu_item_id=item_pepperoni.id, branch_id=b1.id, stock_quantity=30)
        session.add(stock_pepperoni)

        # 4. Fettuccine Alfredo
        item_alfredo = MenuItem(
            category_id=cat_b1_pasta.id,
            name="Fettuccine Alfredo",
            description="Handmade fettuccine ribbons tossed in a velvety parmesan cream sauce.",
            base_price=13.50,
            is_available=True,
        )
        session.add(item_alfredo)
        await session.flush()
        variants_alfredo = [
            MenuItemVariant(menu_item_id=item_alfredo.id, variant_type="spice_level", variant_name="Mild", price_delta=0.00),
            MenuItemVariant(menu_item_id=item_alfredo.id, variant_type="spice_level", variant_name="Spicy", price_delta=0.50),
        ]
        stock_alfredo = MenuItemStock(menu_item_id=item_alfredo.id, branch_id=b1.id, stock_quantity=25)
        session.add_all(variants_alfredo + [stock_alfredo])

        # 5. Artisan Lemonade
        item_lemonade = MenuItem(
            category_id=cat_b1_drinks.id,
            name="Artisan Lemonade",
            description="Freshly squeezed lemons infused with fresh mint leaves and wildflower honey.",
            base_price=4.50,
            is_available=True,
        )
        session.add(item_lemonade)
        await session.flush()
        stock_lemonade = MenuItemStock(menu_item_id=item_lemonade.id, branch_id=b1.id, stock_quantity=50)
        session.add(stock_lemonade)

        # 6. Molten Lava Cake (LOW STOCK = 1)
        item_lava_cake = MenuItem(
            category_id=cat_b1_desserts.id,
            name="Molten Chocolate Lava Cake",
            description="Warm dark chocolate cake with a molten truffle center, served with vanilla bean gelato.",
            base_price=8.00,
            is_available=True,
        )
        session.add(item_lava_cake)
        await session.flush()
        stock_lava_cake = MenuItemStock(menu_item_id=item_lava_cake.id, branch_id=b1.id, stock_quantity=1)
        session.add(stock_lava_cake)

        # Items for Uptown Terrace
        item_uptown_pizza = MenuItem(
            category_id=cat_b2_pizza.id,
            name="Prosciutto & Arugula Pizza",
            description="Aged prosciutto di Parma, wild baby arugula, shaved parmesan, and balsamic glaze.",
            base_price=17.00,
            is_available=True,
        )
        session.add(item_uptown_pizza)
        await session.flush()
        stock_uptown_pizza = MenuItemStock(menu_item_id=item_uptown_pizza.id, branch_id=b2.id, stock_quantity=30)
        session.add(stock_uptown_pizza)

        item_uptown_drink = MenuItem(
            category_id=cat_b2_drinks.id,
            name="Sparkling Hibiscus Cooler",
            description="Cold-brewed hibiscus tea, sparkling mineral water, fresh lime, and organic agave.",
            base_price=5.50,
            is_available=True,
        )
        session.add(item_uptown_drink)
        await session.flush()
        stock_uptown_drink = MenuItemStock(menu_item_id=item_uptown_drink.id, branch_id=b2.id, stock_quantity=45)
        session.add(stock_uptown_drink)

        print("Seeding Staff and Customer Accounts...")
        admin_user = StaffUser(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
            branch_id=None,  # All branches
        )
        downtown_staff = StaffUser(
            username="downtown_staff",
            password_hash=get_password_hash("staff123"),
            role="staff",
            branch_id=b1.id,
        )
        uptown_staff = StaffUser(
            username="uptown_staff",
            password_hash=get_password_hash("staff123"),
            role="staff",
            branch_id=b2.id,
        )
        customer = Customer(
            name="Alice Johnson",
            email="customer@example.com",
            password_hash=get_password_hash("customer123"),
            phone="+1-555-1234",
        )
        session.add_all([admin_user, downtown_staff, uptown_staff, customer])

        await session.commit()
        print("Database seeded successfully with branches, tables, menu, inventory, staff, and customer!")


if __name__ == "__main__":
    asyncio.run(seed_data())
