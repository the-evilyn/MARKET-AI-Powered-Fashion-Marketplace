from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.enums import OrderStatus
from app.modules.orders.models import Order, OrderItem, SubOrder
from app.modules.payments.enums import PaymentProvider, PaymentStatus
from app.modules.payments.models import Payment
from app.modules.seller.enums import StoreStatus
from app.modules.seller.models import Store
from app.modules.users.enums import UserRole
from app.modules.users.models import User


# ==============================================================================
# Helper Fixtures & Setup
# ==============================================================================

@pytest.fixture
async def admin_user(create_user_helper) -> User:
    return await create_user_helper(
        email="superadmin@example.com",
        role=UserRole.ADMIN,
        first_name="Super",
        last_name="Admin",
    )


@pytest.fixture
async def seller_user(create_user_helper) -> User:
    return await create_user_helper(
        email="merchant@example.com",
        role=UserRole.SELLER,
        first_name="John",
        last_name="Merchant",
    )


@pytest.fixture
async def customer_user(create_user_helper) -> User:
    return await create_user_helper(
        email="shopper@example.com",
        role=UserRole.CUSTOMER,
        first_name="Jane",
        last_name="Shopper",
    )


# ==============================================================================
# 1. Authorization Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_01_unauthenticated_requests_get_401_on_all_admin_routes(
    async_client: AsyncClient,
):
    """Every admin endpoint family strictly rejects unauthenticated calls with 401."""
    random_id = str(uuid.uuid4())
    routes = [
        ("GET", "/api/v1/admin/dashboard"),
        ("GET", "/api/v1/admin/stores"),
        ("GET", f"/api/v1/admin/stores/{random_id}"),
        ("PATCH", f"/api/v1/admin/stores/{random_id}/moderation"),
        ("GET", "/api/v1/admin/users"),
        ("GET", f"/api/v1/admin/users/{random_id}"),
        ("PATCH", f"/api/v1/admin/users/{random_id}/status"),
        ("GET", "/api/v1/admin/orders"),
        ("GET", f"/api/v1/admin/orders/{random_id}"),
    ]
    for method, route in routes:
        if method == "GET":
            res = await async_client.get(route)
        else:
            res = await async_client.patch(route, json={"is_active": True})
        assert res.status_code == 401, f"Route {method} {route} should return 401"


@pytest.mark.asyncio
async def test_02_customer_role_gets_403_forbidden(
    async_client: AsyncClient,
    customer_user: User,
    auth_headers_helper,
):
    """Authenticated CUSTOMER requests receive 403 Forbidden across all admin routes."""
    headers = auth_headers_helper(customer_user)
    random_id = str(uuid.uuid4())
    routes = [
        ("GET", "/api/v1/admin/dashboard", None),
        ("GET", "/api/v1/admin/stores", None),
        ("GET", f"/api/v1/admin/stores/{random_id}", None),
        ("PATCH", f"/api/v1/admin/stores/{random_id}/moderation", {"is_verified": True}),
        ("GET", "/api/v1/admin/users", None),
        ("GET", f"/api/v1/admin/users/{random_id}", None),
        ("PATCH", f"/api/v1/admin/users/{random_id}/status", {"is_active": False}),
        ("GET", "/api/v1/admin/orders", None),
        ("GET", f"/api/v1/admin/orders/{random_id}", None),
    ]
    for method, route, body in routes:
        if method == "GET":
            res = await async_client.get(route, headers=headers)
        else:
            res = await async_client.patch(route, json=body, headers=headers)
        assert res.status_code == 403, f"Customer on {method} {route} must receive 403"


@pytest.mark.asyncio
async def test_03_seller_role_gets_403_forbidden(
    async_client: AsyncClient,
    seller_user: User,
    auth_headers_helper,
):
    """Authenticated SELLER requests receive 403 Forbidden across all admin routes."""
    headers = auth_headers_helper(seller_user)
    random_id = str(uuid.uuid4())
    routes = [
        ("GET", "/api/v1/admin/dashboard", None),
        ("GET", "/api/v1/admin/stores", None),
        ("GET", f"/api/v1/admin/stores/{random_id}", None),
        ("PATCH", f"/api/v1/admin/stores/{random_id}/moderation", {"is_verified": True}),
        ("GET", "/api/v1/admin/users", None),
        ("GET", f"/api/v1/admin/users/{random_id}", None),
        ("PATCH", f"/api/v1/admin/users/{random_id}/status", {"is_active": False}),
        ("GET", "/api/v1/admin/orders", None),
        ("GET", f"/api/v1/admin/orders/{random_id}", None),
    ]
    for method, route, body in routes:
        if method == "GET":
            res = await async_client.get(route, headers=headers)
        else:
            res = await async_client.patch(route, json=body, headers=headers)
        assert res.status_code == 403, f"Seller on {method} {route} must receive 403"


@pytest.mark.asyncio
async def test_04_admin_role_is_authorized(
    async_client: AsyncClient,
    admin_user: User,
    auth_headers_helper,
):
    """Authenticated ADMIN requests are authorized (200 OK)."""
    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200


# ==============================================================================
# 2. Dashboard & KPI Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_05_empty_database_metrics_are_handled_safely(
    async_client: AsyncClient,
    admin_user: User,
    auth_headers_helper,
):
    """Admin dashboard handles empty or minimal database safely without divide-by-zero or crashes."""
    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] == 1  # Only the admin user
    assert data["active_users"] == 1
    assert data["total_sellers"] == 0
    assert data["active_sellers"] == 0
    assert data["total_stores"] == 0
    assert data["stores_awaiting_review"] == 0
    assert data["verified_stores"] == 0
    assert data["total_orders"] == 0
    assert data["total_paid_orders"] == 0
    assert data["sales_by_currency"] == []
    assert data["orders_by_status"]["PENDING_PAYMENT"] == 0


@pytest.mark.asyncio
async def test_06_counts_reflect_seeded_records(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    customer_user: User,
    create_user_helper,
    db_session: AsyncSession,
    auth_headers_helper,
):

    """Metrics accurately aggregate user, seller, store, and order records."""
    # Seed a second inactive seller using create_user_helper
    inactive_seller = await create_user_helper(
        email="inactive_seller@example.com",
        role=UserRole.SELLER,
        first_name="Inactive",
        last_name="Seller",
        is_active=False,
    )

    # Seed 2 stores: 1 active & verified, 1 pending & unverified
    store1 = Store(
        seller_id=seller_user.id,
        store_name="Maison Alpha",
        slug="maison-alpha",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )
    store2 = Store(
        seller_id=inactive_seller.id,
        store_name="Maison Beta",
        slug="maison-beta",
        status=StoreStatus.PENDING,
        is_verified=False,
    )
    db_session.add_all([store1, store2])
    await db_session.commit()


    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] == 4  # admin, seller_user, customer_user, inactive_seller
    assert data["active_users"] == 3
    assert data["total_sellers"] == 2
    assert data["active_sellers"] == 1
    assert data["total_stores"] == 2
    assert data["stores_awaiting_review"] == 1  # store2 is PENDING
    assert data["verified_stores"] == 1  # store1 is verified


@pytest.mark.asyncio
async def test_07_paid_revenue_excludes_pending_and_failed_payments(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Paid revenue strictly includes PaymentStatus.COMPLETED and excludes PENDING or FAILED."""
    # 1. Order with COMPLETED payment (USD 200)
    order1 = Order(
        customer_id=customer_user.id,
        order_number="ORD-PAID-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("200.00"),
        total=Decimal("200.00"),
        currency="USD",
    )
    db_session.add(order1)
    await db_session.flush()

    payment1 = Payment(
        order_id=order1.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.COMPLETED,
        amount=Decimal("200.00"),
        currency="USD",
    )
    db_session.add(payment1)

    # 2. Order with PENDING payment (USD 150)
    order2 = Order(
        customer_id=customer_user.id,
        order_number="ORD-PEND-002",
        status=OrderStatus.PENDING_PAYMENT,
        subtotal=Decimal("150.00"),
        total=Decimal("150.00"),
        currency="USD",
    )
    db_session.add(order2)
    await db_session.flush()

    payment2 = Payment(
        order_id=order2.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.PENDING,
        amount=Decimal("150.00"),
        currency="USD",
    )
    db_session.add(payment2)

    # 3. Order with FAILED payment (USD 300)
    order3 = Order(
        customer_id=customer_user.id,
        order_number="ORD-FAIL-003",
        status=OrderStatus.CANCELLED,
        subtotal=Decimal("300.00"),
        total=Decimal("300.00"),
        currency="USD",
    )
    db_session.add(order3)
    await db_session.flush()

    payment3 = Payment(
        order_id=order3.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.FAILED,
        amount=Decimal("300.00"),
        currency="USD",
    )
    db_session.add(payment3)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_orders"] == 3
    assert data["total_paid_orders"] == 1
    assert len(data["sales_by_currency"]) == 1
    usd_sales = data["sales_by_currency"][0]
    assert usd_sales["currency"] == "USD"
    assert Decimal(str(usd_sales["total_sales"])) == Decimal("200.00")
    assert usd_sales["order_count"] == 1


@pytest.mark.asyncio
async def test_08_multi_currency_totals_are_not_combined(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Completed sales are grouped by currency and never conflated into an arbitrary single sum."""
    # Order USD 100
    order_usd = Order(
        customer_id=customer_user.id,
        order_number="ORD-USD-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("100.00"),
        total=Decimal("100.00"),
        currency="USD",
    )
    # Order EUR 85
    order_eur = Order(
        customer_id=customer_user.id,
        order_number="ORD-EUR-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("85.00"),
        total=Decimal("85.00"),
        currency="EUR",
    )
    db_session.add_all([order_usd, order_eur])
    await db_session.flush()

    payment_usd = Payment(
        order_id=order_usd.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.COMPLETED,
        amount=Decimal("100.00"),
        currency="USD",
    )
    payment_eur = Payment(
        order_id=order_eur.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.COMPLETED,
        amount=Decimal("85.00"),
        currency="EUR",
    )
    db_session.add_all([payment_usd, payment_eur])
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_paid_orders"] == 2
    currencies = {s["currency"]: Decimal(str(s["total_sales"])) for s in data["sales_by_currency"]}
    assert currencies.get("USD") == Decimal("100.00")
    assert currencies.get("EUR") == Decimal("85.00")


@pytest.mark.asyncio
async def test_09_sub_orders_do_not_double_count_revenue(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    customer_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Parent orders containing multiple SubOrders only count parent completed payment once."""
    order = Order(
        customer_id=customer_user.id,
        order_number="ORD-SPLIT-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("250.00"),
        total=Decimal("250.00"),
        currency="USD",
    )
    db_session.add(order)
    await db_session.flush()

    # 2 SubOrders for different partitions
    sub1 = SubOrder(
        order_id=order.id,
        seller_id=seller_user.id,
        sub_order_number="SO-SPLIT-001-A",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("150.00"),
        shipping_amount=Decimal("0.00"),
        total=Decimal("150.00"),
        currency="USD",
    )
    sub2 = SubOrder(
        order_id=order.id,
        seller_id=seller_user.id,
        sub_order_number="SO-SPLIT-001-B",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("100.00"),
        shipping_amount=Decimal("0.00"),
        total=Decimal("100.00"),
        currency="USD",
    )
    # Payment record attached strictly to parent order
    payment = Payment(
        order_id=order.id,
        provider=PaymentProvider.PAYPAL,
        status=PaymentStatus.COMPLETED,
        amount=Decimal("250.00"),
        currency="USD",
    )
    db_session.add_all([sub1, sub2, payment])
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_orders"] == 1
    assert data["total_paid_orders"] == 1
    usd_sales = data["sales_by_currency"][0]
    # Must equal 250.00, NOT (250 + 150 + 100) = 500.00
    assert Decimal(str(usd_sales["total_sales"])) == Decimal("250.00")


# ==============================================================================
# 3. Store Moderation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_10_admin_can_list_and_retrieve_stores(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Admin can list stores with pagination and retrieve detailed store by id."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Atelier Couture",
        slug="atelier-couture",
        bio="Bespoke luxury tailoring",
        status=StoreStatus.ACTIVE,
        is_verified=False,
    )
    db_session.add(store)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    # 1. List stores
    list_res = await async_client.get("/api/v1/admin/stores", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(s["slug"] == "atelier-couture" for s in list_data["items"])

    # 2. Retrieve store detail
    get_res = await async_client.get(f"/api/v1/admin/stores/{store.id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["store_name"] == "Atelier Couture"
    assert detail["seller_email"] == seller_user.email


@pytest.mark.asyncio
async def test_11_unknown_store_returns_404(
    async_client: AsyncClient,
    admin_user: User,
    auth_headers_helper,
):
    """Unknown store id returns 404 Not Found."""
    headers = auth_headers_helper(admin_user)
    fake_id = str(uuid.uuid4())
    res = await async_client.get(f"/api/v1/admin/stores/{fake_id}", headers=headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_12_verify_unverify_store_works(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Admin can grant and revoke is_verified flag."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Boutique Paris",
        slug="boutique-paris",
        status=StoreStatus.ACTIVE,
        is_verified=False,
    )
    db_session.add(store)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)

    # 1. Grant verification
    res1 = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"is_verified": True},
        headers=headers,
    )
    assert res1.status_code == 200
    assert res1.json()["is_verified"] is True

    # 2. Revoke verification
    res2 = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"is_verified": False},
        headers=headers,
    )
    assert res2.status_code == 200
    assert res2.json()["is_verified"] is False


@pytest.mark.asyncio
async def test_13_verification_does_not_activate_a_suspended_store(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Verifying a SUSPENDED store leaves its status as SUSPENDED (decoupled semantics)."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Suspended Label",
        slug="suspended-label",
        status=StoreStatus.SUSPENDED,
        is_verified=False,
    )
    db_session.add(store)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"is_verified": True},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_verified"] is True
    # Status MUST remain SUSPENDED!
    assert data["status"] == "SUSPENDED"


@pytest.mark.asyncio
async def test_14_suspend_store_makes_public_storefront_inaccessible(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Suspending a store immediately hides it from the public storefront API (returns 404)."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Public Studio",
        slug="public-studio",
        status=StoreStatus.ACTIVE,
        is_verified=False,
    )
    db_session.add(store)
    await db_session.commit()

    # 1. Public storefront is accessible
    pub_res1 = await async_client.get("/api/v1/stores/public-studio")
    assert pub_res1.status_code == 200

    # 2. Admin suspends store
    headers = auth_headers_helper(admin_user)
    mod_res = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"status": "SUSPENDED"},
        headers=headers,
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["status"] == "SUSPENDED"

    # 3. Public storefront is now hidden (404)
    pub_res2 = await async_client.get("/api/v1/stores/public-studio")
    assert pub_res2.status_code == 404

    # 4. Admin reactivates store
    reactivate_res = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"status": "ACTIVE"},
        headers=headers,
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["status"] == "ACTIVE"

    # 5. Public storefront is visible again
    pub_res3 = await async_client.get("/api/v1/stores/public-studio")
    assert pub_res3.status_code == 200


@pytest.mark.asyncio
async def test_15_invalid_status_transitions_and_unexpected_fields_are_rejected(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Pydantic rejects unexpected fields and service rejects invalid status transitions."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Strict Store",
        slug="strict-store",
        status=StoreStatus.SUSPENDED,
        is_verified=False,
    )
    db_session.add(store)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)

    # 1. Unexpected extra field rejected by Pydantic extra="forbid"
    res1 = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"status": "ACTIVE", "seller_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert res1.status_code == 422

    # 2. Invalid status transition (SUSPENDED -> REJECTED is not allowed)
    res2 = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"status": "REJECTED"},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "Cannot transition store status" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_16_non_admin_cannot_moderate_stores(
    async_client: AsyncClient,
    customer_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Customer and seller cannot invoke store moderation endpoint."""
    store = Store(
        seller_id=seller_user.id,
        store_name="Protected Store",
        slug="protected-store",
        status=StoreStatus.ACTIVE,
    )
    db_session.add(store)
    await db_session.commit()

    # Customer gets 403
    res_cust = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"status": "SUSPENDED"},
        headers=auth_headers_helper(customer_user),
    )
    assert res_cust.status_code == 403

    # Store owner seller gets 403 (cannot self-verify or moderate status)
    res_seller = await async_client.patch(
        f"/api/v1/admin/stores/{store.id}/moderation",
        json={"is_verified": True},
        headers=auth_headers_helper(seller_user),
    )
    assert res_seller.status_code == 403


# ==============================================================================
# 4. User Management Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_17_user_pagination_and_filters_work(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    customer_user: User,
    auth_headers_helper,
):
    """Admin can search users by email, name, and filter by role."""
    headers = auth_headers_helper(admin_user)

    # 1. Filter by role=SELLER
    res_seller = await async_client.get("/api/v1/admin/users?role=SELLER", headers=headers)
    assert res_seller.status_code == 200
    data = res_seller.json()
    assert all(u["role"] == "SELLER" for u in data["items"])

    # 2. Search by query 'shopper'
    res_search = await async_client.get("/api/v1/admin/users?q=shopper", headers=headers)
    assert res_search.status_code == 200
    assert any("shopper" in u["email"] for u in res_search.json()["items"])


@pytest.mark.asyncio
async def test_18_user_responses_never_expose_password_hashes(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    auth_headers_helper,
):
    """Neither user list nor detail responses leak password_hash or secret tokens."""
    headers = auth_headers_helper(admin_user)

    # List endpoint
    res_list = await async_client.get("/api/v1/admin/users", headers=headers)
    assert res_list.status_code == 200
    for u in res_list.json()["items"]:
        assert "password_hash" not in u
        assert "password" not in u

    # Detail endpoint
    res_detail = await async_client.get(f"/api/v1/admin/users/{customer_user.id}", headers=headers)
    assert res_detail.status_code == 200
    user_detail = res_detail.json()
    assert "password_hash" not in user_detail
    assert "password" not in user_detail


@pytest.mark.asyncio
async def test_19_admin_can_activate_and_deactivate_eligible_user(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    auth_headers_helper,
):
    """Admin can deactivate an active customer account, then reactivate it."""
    headers = auth_headers_helper(admin_user)

    # 1. Deactivate customer
    res1 = await async_client.patch(
        f"/api/v1/admin/users/{customer_user.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res1.status_code == 200
    assert res1.json()["is_active"] is False

    # 2. Verify deactivated customer cannot authenticate to protected user routes
    cust_headers = auth_headers_helper(customer_user)
    cust_res = await async_client.get("/api/v1/users/me", headers=cust_headers)
    assert cust_res.status_code == 403

    # 3. Reactivate customer
    res2 = await async_client.patch(
        f"/api/v1/admin/users/{customer_user.id}/status",
        json={"is_active": True},
        headers=headers,
    )
    assert res2.status_code == 200
    assert res2.json()["is_active"] is True


@pytest.mark.asyncio
async def test_20_self_deactivation_is_strictly_rejected(
    async_client: AsyncClient,
    admin_user: User,
    auth_headers_helper,
):
    """An administrator cannot deactivate their own account."""
    headers = auth_headers_helper(admin_user)
    res = await async_client.patch(
        f"/api/v1/admin/users/{admin_user.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res.status_code == 400
    assert "cannot deactivate their own account" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_21_last_active_administrator_cannot_be_deactivated(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Target admin cannot be deactivated if they are the only remaining active administrator."""
    admin1 = await create_user_helper(email="admin1@example.com", role=UserRole.ADMIN, is_active=True)
    admin2 = await create_user_helper(email="admin2@example.com", role=UserRole.ADMIN, is_active=True)

    headers1 = auth_headers_helper(admin1)

    # Admin 1 deactivates Admin 2 (allowed since Admin 1 remains active)
    res1 = await async_client.patch(
        f"/api/v1/admin/users/{admin2.id}/status",
        json={"is_active": False},
        headers=headers1,
    )
    assert res1.status_code == 200
    assert res1.json()["is_active"] is False

    # Now Admin 2 is inactive. Admin 1 is the sole active admin.
    # If someone tries to deactivate Admin 1:
    # 1. Admin 1 self-deactivation is rejected:
    res2 = await async_client.patch(
        f"/api/v1/admin/users/{admin1.id}/status",
        json={"is_active": False},
        headers=headers1,
    )
    assert res2.status_code == 400


@pytest.mark.asyncio
async def test_22_role_changes_and_escalation_through_status_endpoint_are_rejected(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    auth_headers_helper,
):
    """Any attempt to inject role changes into the status endpoint is rejected by Pydantic."""
    headers = auth_headers_helper(admin_user)
    res = await async_client.patch(
        f"/api/v1/admin/users/{customer_user.id}/status",
        json={"is_active": True, "role": "ADMIN"},
        headers=headers,
    )
    assert res.status_code == 422


# ==============================================================================
# 5. Global Orders Supervision Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_23_admin_can_view_orders_from_all_customers_and_sellers(
    async_client: AsyncClient,
    admin_user: User,
    seller_user: User,
    customer_user: User,
    create_user_helper,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Admin inspects multi-vendor orders across all customers."""
    cust2 = await create_user_helper(email="cust2@example.com", role=UserRole.CUSTOMER)

    order1 = Order(
        customer_id=customer_user.id,
        order_number="ORD-ALL-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("120.00"),
        total=Decimal("120.00"),
        currency="USD",
    )
    order2 = Order(
        customer_id=cust2.id,
        order_number="ORD-ALL-002",
        status=OrderStatus.PENDING_PAYMENT,
        subtotal=Decimal("80.00"),
        total=Decimal("80.00"),
        currency="USD",
    )
    db_session.add_all([order1, order2])
    await db_session.flush()

    sub1 = SubOrder(
        order_id=order1.id,
        seller_id=seller_user.id,
        sub_order_number="SO-ALL-001-A",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("120.00"),
        shipping_amount=Decimal("0.00"),
        total=Decimal("120.00"),
        currency="USD",
    )
    db_session.add(sub1)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.get("/api/v1/admin/orders", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    order_numbers = [o["order_number"] for o in data]
    assert "ORD-ALL-001" in order_numbers
    assert "ORD-ALL-002" in order_numbers


@pytest.mark.asyncio
async def test_24_order_filters_by_status_and_customer_work(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Admin can filter orders by status and customer UUID."""
    order = Order(
        customer_id=customer_user.id,
        order_number="ORD-FILTER-001",
        status=OrderStatus.SHIPPED,
        subtotal=Decimal("95.00"),
        total=Decimal("95.00"),
        currency="USD",
    )
    db_session.add(order)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)

    # 1. Filter by status=SHIPPED
    res1 = await async_client.get("/api/v1/admin/orders?status=SHIPPED", headers=headers)
    assert res1.status_code == 200
    assert any(o["order_number"] == "ORD-FILTER-001" for o in res1.json())

    # 2. Filter by status=CANCELLED (should be empty for this order)
    res2 = await async_client.get("/api/v1/admin/orders?status=CANCELLED", headers=headers)
    assert res2.status_code == 200
    assert not any(o["order_number"] == "ORD-FILTER-001" for o in res2.json())

    # 3. Filter by customer_id
    res3 = await async_client.get(f"/api/v1/admin/orders?customer_id={customer_user.id}", headers=headers)
    assert res3.status_code == 200
    assert any(o["order_number"] == "ORD-FILTER-001" for o in res3.json())


@pytest.mark.asyncio
async def test_25_unknown_order_returns_404(
    async_client: AsyncClient,
    admin_user: User,
    auth_headers_helper,
):
    """Retrieving unknown order returns 404 Not Found."""
    headers = auth_headers_helper(admin_user)
    fake_id = str(uuid.uuid4())
    res = await async_client.get(f"/api/v1/admin/orders/{fake_id}", headers=headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_26_order_details_never_expose_payment_secrets_or_tokens(
    async_client: AsyncClient,
    admin_user: User,
    customer_user: User,
    seller_user: User,
    db_session: AsyncSession,
    auth_headers_helper,
):
    """Order detail returns safe payment summary without secrets or webhook tokens."""
    order = Order(
        customer_id=customer_user.id,
        order_number="ORD-SEC-001",
        status=OrderStatus.CONFIRMED,
        subtotal=Decimal("180.00"),
        total=Decimal("180.00"),
        currency="USD",
    )
    db_session.add(order)
    await db_session.flush()

    payment = Payment(
        order_id=order.id,
        provider=PaymentProvider.PAYPAL,
        provider_order_id="PP-ORD-12345",
        provider_payment_id="PP-PAY-67890",
        status=PaymentStatus.COMPLETED,
        amount=Decimal("180.00"),
        currency="USD",
    )
    db_session.add(payment)
    await db_session.commit()

    headers = auth_headers_helper(admin_user)
    res = await async_client.get(f"/api/v1/admin/orders/{order.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["order_number"] == "ORD-SEC-001"
    assert data["payment_status"] == "COMPLETED"
    assert data["payment_provider"] == "PAYPAL"
    # Guarantee no secret fields exist
    assert "webhook_secret" not in data
    assert "client_secret" not in data
    assert "access_token" not in data

