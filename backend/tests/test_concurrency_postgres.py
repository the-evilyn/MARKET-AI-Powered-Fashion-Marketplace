import asyncio
from decimal import Decimal
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.modules.cart.enums import CartStatus
from app.modules.cart.models import Cart, CartItem
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Brand, Category, Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.inventory.service import InventoryService
from app.modules.orders.models import Order
from app.modules.orders.service import CheckoutService
from app.modules.users.enums import UserRole
from app.modules.users.models import User


# Connect directly to real PostgreSQL container configured in Settings
settings = get_settings()
pg_engine = create_async_engine(settings.DATABASE_URL, echo=False)
PgSessionLocal = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.mark.asyncio
async def test_postgres_concurrent_checkout_and_inventory_lifecycle():
    """
    Mandatory Section 20 PostgreSQL Concurrency & Inventory Lifecycle Test.
    1. Sets initial stock = 5 (quantity_on_hand=5, quantity_reserved=0).
    2. Customer A cart = 4, Customer B cart = 3.
    3. Runs both checkouts concurrently against PostgreSQL with row-level locks.
    4. Proves exactly one succeeds and one fails.
    5. Proves quantity_on_hand=5, quantity_reserved=4, available=1.
    6. Simulates successful capture -> quantity_on_hand=1, quantity_reserved=0.
    7. Tests failure/cancellation scenario -> reservation released back to 5.
    """
    async with PgSessionLocal() as seed_session:
        # 1. Create seller and customers
        suffix = uuid.uuid4().hex[:6]
        seller = User(
            id=uuid.uuid4(),
            email=f"seller_conc_{suffix}@example.com",
            password_hash=hash_password("Pass123!"),
            role=UserRole.SELLER,
            first_name="Seller",
            last_name="Conc",
            is_active=True,
            is_verified=True,
        )
        cust_a = User(
            id=uuid.uuid4(),
            email=f"cust_a_{suffix}@example.com",
            password_hash=hash_password("Pass123!"),
            role=UserRole.CUSTOMER,
            first_name="Customer",
            last_name="A",
            is_active=True,
            is_verified=True,
        )
        cust_b = User(
            id=uuid.uuid4(),
            email=f"cust_b_{suffix}@example.com",
            password_hash=hash_password("Pass123!"),
            role=UserRole.CUSTOMER,
            first_name="Customer",
            last_name="B",
            is_active=True,
            is_verified=True,
        )
        seed_session.add_all([seller, cust_a, cust_b])

        # 2. Brand & Category
        brand = Brand(
            id=uuid.uuid4(),
            name=f"Brand {suffix}",
            slug=f"brand-{suffix}",
            is_active=True,
        )
        cat = Category(
            id=uuid.uuid4(),
            name=f"Cat {suffix}",
            slug=f"cat-{suffix}",
            is_active=True,
        )
        seed_session.add_all([brand, cat])

        # 3. Product & Variant 1
        prod1 = Product(
            id=uuid.uuid4(),
            seller_id=seller.id,
            brand_id=brand.id,
            category_id=cat.id,
            name=f"Conc Jacket {suffix}",
            slug=f"conc-jacket-{suffix}",
            base_price=Decimal("80.00"),
            status=ProductStatus.ACTIVE,
            is_active=True,
        )
        seed_session.add(prod1)

        var1 = ProductVariant(
            id=uuid.uuid4(),
            product_id=prod1.id,
            sku=f"SKU-CONC-{suffix}",
            price=Decimal("80.00"),
            is_active=True,
        )
        seed_session.add(var1)

        # 4. Inventory item with on_hand=5, reserved=0
        inv1 = InventoryItem(
            id=uuid.uuid4(),
            variant_id=var1.id,
            quantity_on_hand=5,
            quantity_reserved=0,
            low_stock_threshold=2,
        )
        seed_session.add(inv1)

        # 5. Customer A cart with 4 units
        cart_a = Cart(id=uuid.uuid4(), customer_id=cust_a.id, status=CartStatus.ACTIVE)
        seed_session.add(cart_a)
        item_a = CartItem(
            id=uuid.uuid4(),
            cart_id=cart_a.id,
            variant_id=var1.id,
            quantity=4,
            unit_price=Decimal("80.00"),
        )
        seed_session.add(item_a)

        # 6. Customer B cart with 3 units
        cart_b = Cart(id=uuid.uuid4(), customer_id=cust_b.id, status=CartStatus.ACTIVE)
        seed_session.add(cart_b)
        item_b = CartItem(
            id=uuid.uuid4(),
            cart_id=cart_b.id,
            variant_id=var1.id,
            quantity=3,
            unit_price=Decimal("80.00"),
        )
        seed_session.add(item_b)

        await seed_session.commit()

    # -------------------------------------------------------------------------
    # SCENARIO 1: Concurrent checkout with independent PostgreSQL sessions
    # -------------------------------------------------------------------------
    async def run_checkout(customer_id: uuid.UUID):
        async with PgSessionLocal() as session:
            return await CheckoutService.checkout(session, customer_id)

    results = await asyncio.gather(
        run_checkout(cust_a.id),
        run_checkout(cust_b.id),
        return_exceptions=True,
    )

    # Exactly one succeeded and one failed
    successes = [r for r in results if isinstance(r, Order)]
    failures = [r for r in results if isinstance(r, (HTTPException, Exception))]

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, f"Expected 1 failure, got {len(failures)}: {results}"

    failed_ex = failures[0]
    assert isinstance(failed_ex, HTTPException)
    assert failed_ex.status_code == 400
    assert "insufficient stock" in failed_ex.detail.lower()

    winning_order = successes[0]

    # Verify inventory in PostgreSQL immediately after reservation:
    async with PgSessionLocal() as verify_session:
        res = await verify_session.execute(
            select(InventoryItem).where(InventoryItem.variant_id == var1.id)
        )
        inv_after_chk = res.scalar_one()

        # On hand must still be 5! Reserved must be 4 (or 3, whichever won)!
        assert inv_after_chk.quantity_on_hand == 5
        reserved_qty = inv_after_chk.quantity_reserved
        assert reserved_qty in (3, 4)
        assert inv_after_chk.quantity_available == 5 - reserved_qty

        # Simulate successful payment capture for winning customer:
        await InventoryService.finalize_order_inventory(verify_session, winning_order.id)
        await verify_session.commit()

        # Re-check inventory: on_hand decremented, reserved zeroed out!
        res2 = await verify_session.execute(
            select(InventoryItem).where(InventoryItem.variant_id == var1.id)
        )
        inv_after_pay = res2.scalar_one()
        assert inv_after_pay.quantity_reserved == 0
        assert inv_after_pay.quantity_on_hand == 5 - reserved_qty
        assert inv_after_pay.quantity_available == 5 - reserved_qty

    # -------------------------------------------------------------------------
    # SCENARIO 2: Failure / Cancellation scenario (reservation released)
    # -------------------------------------------------------------------------
    async with PgSessionLocal() as s2:
        # Create fresh variant with stock = 5
        var2 = ProductVariant(
            id=uuid.uuid4(),
            product_id=prod1.id,
            sku=f"SKU-REL-{suffix}",
            price=Decimal("60.00"),
            is_active=True,
        )
        s2.add(var2)
        inv2 = InventoryItem(
            id=uuid.uuid4(),
            variant_id=var2.id,
            quantity_on_hand=5,
            quantity_reserved=0,
            low_stock_threshold=2,
        )
        s2.add(inv2)

        # New cart with 4 items for customer A
        cart_a2 = Cart(id=uuid.uuid4(), customer_id=cust_a.id, status=CartStatus.ACTIVE)
        s2.add(cart_a2)
        item_a2 = CartItem(
            id=uuid.uuid4(),
            cart_id=cart_a2.id,
            variant_id=var2.id,
            quantity=4,
            unit_price=Decimal("60.00"),
        )
        s2.add(item_a2)
        await s2.commit()

    # Checkout 4 units
    async with PgSessionLocal() as s2_chk:
        order2 = await CheckoutService.checkout(s2_chk, cust_a.id)
        assert order2.id is not None

    # Check reservation: on_hand=5, reserved=4
    async with PgSessionLocal() as s2_verify:
        res = await s2_verify.execute(
            select(InventoryItem).where(InventoryItem.variant_id == var2.id)
        )
        inv2_res = res.scalar_one()
        assert inv2_res.quantity_on_hand == 5
        assert inv2_res.quantity_reserved == 4
        assert inv2_res.quantity_available == 1

        # Simulate payment failure / cancellation: release reservation
        await InventoryService.release_order_inventory(s2_verify, order2.id)
        await s2_verify.commit()

        # Re-check inventory: on_hand remains 5, reserved returns to 0
        res_rel = await s2_verify.execute(
            select(InventoryItem).where(InventoryItem.variant_id == var2.id)
        )
        inv2_final = res_rel.scalar_one()
        assert inv2_final.quantity_on_hand == 5
        assert inv2_final.quantity_reserved == 0
        assert inv2_final.quantity_available == 5
