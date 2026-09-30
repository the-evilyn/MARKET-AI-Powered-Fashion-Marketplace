from decimal import Decimal
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient

from app.modules.payments.routes import payment_service
from app.modules.users.enums import UserRole
from tests.test_cart import create_catalog_item


async def setup_customer_with_order(
    async_client: AsyncClient,
    s_headers: dict,
    c_headers: dict,
    sku: str = "PAY-TEST-01",
    price: str = "50.00",
    stock_qty: int = 10,
    buy_qty: int = 2,
):
    """Helper to create catalog item, add to cart, checkout and return order dict + variant_id."""
    _, variant_id = await create_catalog_item(
        async_client, s_headers, sku=sku, price=price, stock_qty=stock_qty
    )
    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": buy_qty},
        headers=c_headers,
    )
    chk_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert chk_res.status_code == 201
    return chk_res.json(), variant_id


# ==============================================================================
# Payment Creation Tests (Tests 01 to 09)
# ==============================================================================

@pytest.mark.asyncio
async def test_01_customer_creates_paypal_order_success(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 01: Customer successfully initializes PayPal order for their PENDING_PAYMENT order."""
    seller = await create_user_helper(email="seller_p1@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p1@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P01")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-001", "status": "CREATED"}),
    ):
        res = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["paypal_order_id"] == "PAYPAL-ORDER-001"
        assert data["amount"] == "100.00"
        assert data["currency"] == "USD"
        assert data["provider"] == "PAYPAL"


@pytest.mark.asyncio
async def test_02_customer_cannot_create_payment_for_another_customer_order(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 02: Customer B cannot initiate PayPal payment for Customer A's order (IDOR protection)."""
    seller = await create_user_helper(email="seller_p2@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust_p2a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust_p2b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    ca_headers = auth_headers_helper(cust_a)
    cb_headers = auth_headers_helper(cust_b)

    order_a, _ = await setup_customer_with_order(async_client, s_headers, ca_headers, sku="P02")

    res = await async_client.post(
        "/api/v1/payments/paypal/create-order",
        json={"order_id": order_a["id"]},
        headers=cb_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_03_create_payment_nonexistent_order_returns_404(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 03: Creating PayPal order for a non-existent order ID returns 404."""
    customer = await create_user_helper(email="cust_p3@example.com", role=UserRole.CUSTOMER)
    c_headers = auth_headers_helper(customer)

    res = await async_client.post(
        "/api/v1/payments/paypal/create-order",
        json={"order_id": str(uuid.uuid4())},
        headers=c_headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_04_create_payment_already_confirmed_order_rejected(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 04: Creating payment for an already CONFIRMED order is rejected."""
    seller = await create_user_helper(email="seller_p4@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p4@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P04")

    # Simulate payment creation and capture
    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-004", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(
            return_value={
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": "CAP-004",
                                    "status": "COMPLETED",
                                    "amount": {"value": "100.00", "currency_code": "USD"},
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-004"},
            headers=c_headers,
        )

        # Attempt to create another payment order for the confirmed order
        res = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_05_create_payment_already_cancelled_order_rejected(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 05: Creating payment for a CANCELLED order is rejected."""
    seller = await create_user_helper(email="seller_p5@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p5@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P05")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-005", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        await async_client.post(
            "/api/v1/payments/paypal/cancel",
            json={"paypal_order_id": "PAYPAL-ORDER-005"},
            headers=c_headers,
        )

        # Attempt to create payment on cancelled order
        res = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_06_create_payment_amount_and_currency_authoritative_from_db(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 06: Amount and currency passed to PayPal match the database Order."""
    seller = await create_user_helper(email="seller_p6@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p6@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P06", price="33.50", buy_qty=3
    )
    # 33.50 * 3 = 100.50

    mock_create = AsyncMock(return_value={"id": "PAYPAL-ORDER-006", "status": "CREATED"})
    with patch.object(payment_service.paypal_client, "create_order", new=mock_create):
        res = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res.status_code == 201
        assert mock_create.call_args.kwargs["amount"] == Decimal("100.50")
        assert mock_create.call_args.kwargs["currency"] == "USD"


@pytest.mark.asyncio
async def test_07_duplicate_create_payment_reuses_or_updates_pending_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 07: Retrying create-order for the same pending order updates the pending payment record."""
    seller = await create_user_helper(email="seller_p7@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p7@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P07")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        side_effect=[
            {"id": "PAYPAL-007A", "status": "CREATED"},
            {"id": "PAYPAL-007B", "status": "CREATED"},
        ],
    ):
        res1 = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res1.status_code == 201
        p_id_1 = res1.json()["payment_id"]

        res2 = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        assert res2.status_code == 201
        p_id_2 = res2.json()["payment_id"]
        # Same payment record updated
        assert p_id_1 == p_id_2
        assert res2.json()["paypal_order_id"] == "PAYPAL-007B"


@pytest.mark.asyncio
async def test_08_seller_and_admin_cannot_create_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 08: SELLER and ADMIN cannot invoke customer create-payment endpoint."""
    seller = await create_user_helper(email="seller_p8@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="admin_p8@example.com", role=UserRole.ADMIN)
    s_headers = auth_headers_helper(seller)
    a_headers = auth_headers_helper(admin)

    res_s = await async_client.post(
        "/api/v1/payments/paypal/create-order",
        json={"order_id": str(uuid.uuid4())},
        headers=s_headers,
    )
    assert res_s.status_code == 403

    res_a = await async_client.post(
        "/api/v1/payments/paypal/create-order",
        json={"order_id": str(uuid.uuid4())},
        headers=a_headers,
    )
    assert res_a.status_code == 403


@pytest.mark.asyncio
async def test_09_unauthenticated_cannot_create_payment(async_client: AsyncClient):
    """Test 09: Unauthenticated request to create PayPal order returns 401."""
    res = await async_client.post(
        "/api/v1/payments/paypal/create-order",
        json={"order_id": str(uuid.uuid4())},
    )
    assert res.status_code == 401


# ==============================================================================
# Payment Capture & Inventory Finalization Tests (Tests 10 to 16)
# ==============================================================================

@pytest.mark.asyncio
async def test_10_capture_payment_success_confirms_order_and_finalizes_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 10: Successful capture transitions Order -> CONFIRMED, Payment -> COMPLETED, and finalizes stock."""
    seller = await create_user_helper(email="seller_p10@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p10@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P10", stock_qty=10, buy_qty=3
    )

    # Initial inventory state after checkout reservation: on_hand=10, reserved=3, available=7
    inv_check = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_check.json()["quantity_on_hand"] == 10
    assert inv_check.json()["quantity_reserved"] == 3
    assert inv_check.json()["quantity_available"] == 7

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-010", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(
            return_value={
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": "CAP-010",
                                    "status": "COMPLETED",
                                    "amount": {"value": order["total"], "currency_code": "USD"},
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

        cap_res = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-010"},
            headers=c_headers,
        )
        assert cap_res.status_code == 200
        cap_data = cap_res.json()
        assert cap_data["status"] == "COMPLETED"
        assert cap_data["order_status"] == "CONFIRMED"
        assert cap_data["provider_payment_id"] == "CAP-010"

    # Inventory state after finalization: on_hand=7, reserved=0, available=7
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 7
    assert inv_final.json()["quantity_reserved"] == 0
    assert inv_final.json()["quantity_available"] == 7


@pytest.mark.asyncio
async def test_11_capture_payment_failure_cancels_order_and_releases_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 11: Failed PayPal capture transitions Order -> CANCELLED, Payment -> FAILED, and releases stock."""
    seller = await create_user_helper(email="seller_p11@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p11@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P11", stock_qty=10, buy_qty=3
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-011", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(return_value={"status": "DENIED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

        cap_res = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-011"},
            headers=c_headers,
        )
        assert cap_res.status_code == 200
        cap_data = cap_res.json()
        assert cap_data["status"] == "FAILED"
        assert cap_data["order_status"] == "CANCELLED"

    # Stock is released: on_hand remains 10, reserved=0, available=10
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 10
    assert inv_final.json()["quantity_reserved"] == 0
    assert inv_final.json()["quantity_available"] == 10


@pytest.mark.asyncio
async def test_12_capture_payment_amount_mismatch_rejected_and_rolls_back(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 12: Price tampering protection: if PayPal returns a different captured amount, capture is rejected."""
    seller = await create_user_helper(email="seller_p12@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p12@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P12", price="100.00", stock_qty=5, buy_qty=1
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-012", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(
            return_value={
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": "CAP-012",
                                    "status": "COMPLETED",
                                    "amount": {"value": "1.00", "currency_code": "USD"},  # Tampered
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

        cap_res = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-012"},
            headers=c_headers,
        )
        assert cap_res.status_code == 400
        assert "captured amount does not match" in cap_res.json()["detail"].lower()

    # Stock is safely released
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 5
    assert inv_final.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_13_capture_payment_customer_ownership_enforced(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 13: Customer B cannot capture payment for Customer A's order."""
    seller = await create_user_helper(email="seller_p13@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust_p13a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust_p13b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    ca_headers = auth_headers_helper(cust_a)
    cb_headers = auth_headers_helper(cust_b)

    order_a, _ = await setup_customer_with_order(async_client, s_headers, ca_headers, sku="P13")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-013", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order_a["id"]},
            headers=ca_headers,
        )

    # Cust B attempts to capture Cust A's payment
    res = await async_client.post(
        "/api/v1/payments/paypal/capture",
        json={"paypal_order_id": "PAYPAL-ORDER-013"},
        headers=cb_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_14_capture_payment_idempotent_retry(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 14: Retrying capture on an already confirmed order returns success without double-finalizing stock."""
    seller = await create_user_helper(email="seller_p14@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p14@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P14", stock_qty=10, buy_qty=2
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-014", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(
            return_value={
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": "CAP-014",
                                    "status": "COMPLETED",
                                    "amount": {"value": order["total"], "currency_code": "USD"},
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

        # First capture
        res1 = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-014"},
            headers=c_headers,
        )
        assert res1.status_code == 200

        # Second capture (retry)
        res2 = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-014"},
            headers=c_headers,
        )
        assert res2.status_code == 200
        assert res2.json()["status"] == "COMPLETED"

    # Stock is decremented exactly once: 10 - 2 = 8
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 8
    assert inv_final.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_15_capture_nonexistent_paypal_order_returns_404(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 15: Capturing unknown PayPal order ID returns 404."""
    customer = await create_user_helper(email="cust_p15@example.com", role=UserRole.CUSTOMER)
    c_headers = auth_headers_helper(customer)

    res = await async_client.post(
        "/api/v1/payments/paypal/capture",
        json={"paypal_order_id": "UNKNOWN-PAYPAL-ID"},
        headers=c_headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_16_seller_and_admin_cannot_capture_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 16: SELLER and ADMIN cannot call capture endpoint."""
    seller = await create_user_helper(email="seller_p16@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="admin_p16@example.com", role=UserRole.ADMIN)
    s_headers = auth_headers_helper(seller)
    a_headers = auth_headers_helper(admin)

    res_s = await async_client.post(
        "/api/v1/payments/paypal/capture",
        json={"paypal_order_id": "DUMMY"},
        headers=s_headers,
    )
    assert res_s.status_code == 403

    res_a = await async_client.post(
        "/api/v1/payments/paypal/capture",
        json={"paypal_order_id": "DUMMY"},
        headers=a_headers,
    )
    assert res_a.status_code == 403


# ==============================================================================
# Payment Cancellation & Reservation Release Tests (Tests 17 to 20)
# ==============================================================================

@pytest.mark.asyncio
async def test_17_customer_cancels_payment_releases_reservation_and_cancels_order(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 17: User cancelling payment sets Order -> CANCELLED, Payment -> CANCELLED, and releases stock."""
    seller = await create_user_helper(email="seller_p17@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p17@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P17", stock_qty=10, buy_qty=4
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-017", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

        cancel_res = await async_client.post(
            "/api/v1/payments/paypal/cancel",
            json={"paypal_order_id": "PAYPAL-ORDER-017"},
            headers=c_headers,
        )
        assert cancel_res.status_code == 200
        data = cancel_res.json()
        assert data["status"] == "CANCELLED"
        assert data["order_status"] == "CANCELLED"

    # Reserved stock released back: on_hand=10, reserved=0, available=10
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 10
    assert inv_final.json()["quantity_reserved"] == 0
    assert inv_final.json()["quantity_available"] == 10


@pytest.mark.asyncio
async def test_18_customer_cannot_cancel_another_customer_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 18: Customer B cannot cancel Customer A's payment."""
    seller = await create_user_helper(email="seller_p18@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust_p18a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust_p18b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    ca_headers = auth_headers_helper(cust_a)
    cb_headers = auth_headers_helper(cust_b)

    order_a, _ = await setup_customer_with_order(async_client, s_headers, ca_headers, sku="P18")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-018", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order_a["id"]},
            headers=ca_headers,
        )

    res = await async_client.post(
        "/api/v1/payments/paypal/cancel",
        json={"paypal_order_id": "PAYPAL-ORDER-018"},
        headers=cb_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_19_cancel_payment_idempotent_retry(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 19: Retrying cancel on an already cancelled payment is an idempotent no-op."""
    seller = await create_user_helper(email="seller_p19@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p19@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P19", stock_qty=5, buy_qty=1
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-019", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        res1 = await async_client.post(
            "/api/v1/payments/paypal/cancel",
            json={"paypal_order_id": "PAYPAL-ORDER-019"},
            headers=c_headers,
        )
        assert res1.status_code == 200

        res2 = await async_client.post(
            "/api/v1/payments/paypal/cancel",
            json={"paypal_order_id": "PAYPAL-ORDER-019"},
            headers=c_headers,
        )
        assert res2.status_code == 200
        assert res2.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_20_cannot_cancel_already_confirmed_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 20: Attempting to cancel an already confirmed order raises 400."""
    seller = await create_user_helper(email="seller_p20@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p20@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P20")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-020", "status": "CREATED"}),
    ), patch.object(
        payment_service.paypal_client,
        "capture_order",
        new=AsyncMock(
            return_value={
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "payments": {
                            "captures": [
                                {
                                    "id": "CAP-020",
                                    "status": "COMPLETED",
                                    "amount": {"value": order["total"], "currency_code": "USD"},
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )
        await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": "PAYPAL-ORDER-020"},
            headers=c_headers,
        )

        res = await async_client.post(
            "/api/v1/payments/paypal/cancel",
            json={"paypal_order_id": "PAYPAL-ORDER-020"},
            headers=c_headers,
        )
        assert res.status_code == 400


# ==============================================================================
# Webhook Handling & Idempotency Tests (Tests 21 to 25)
# ==============================================================================

@pytest.mark.asyncio
async def test_21_webhook_capture_completed_confirms_order_and_finalizes_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 21: PAYMENT.CAPTURE.COMPLETED webhook confirms order and finalizes stock."""
    seller = await create_user_helper(email="seller_p21@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p21@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P21", stock_qty=10, buy_qty=3
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-021", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    # Ingest webhook
    webhook_payload = {
        "id": "WH-EVT-021",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAP-WH-021",
            "custom_id": order["id"],
            "status": "COMPLETED",
            "amount": {"value": order["total"], "currency_code": "USD"},
        },
    }

    res = await async_client.post("/api/v1/payments/paypal/webhook", json=webhook_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # Verify order is confirmed
    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "CONFIRMED"
    assert order_check.json()["payment_status"] == "COMPLETED"

    # Stock is finalized
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 7
    assert inv_final.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_22_webhook_capture_denied_cancels_order_and_releases_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 22: PAYMENT.CAPTURE.DENIED webhook cancels order and releases reservation."""
    seller = await create_user_helper(email="seller_p22@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p22@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P22", stock_qty=10, buy_qty=3
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-022", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    webhook_payload = {
        "id": "WH-EVT-022",
        "event_type": "PAYMENT.CAPTURE.DENIED",
        "resource": {
            "id": "CAP-WH-022",
            "custom_id": order["id"],
            "status": "DENIED",
        },
    }

    res = await async_client.post("/api/v1/payments/paypal/webhook", json=webhook_payload)
    assert res.status_code == 200

    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "CANCELLED"
    assert order_check.json()["payment_status"] == "FAILED"

    # Stock released: on_hand=10, reserved=0
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 10
    assert inv_final.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_23_webhook_approval_reversed_cancels_order_and_releases_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 23: CHECKOUT.PAYMENT-APPROVAL.REVERSED webhook cancels order and releases reservation."""
    seller = await create_user_helper(email="seller_p23@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p23@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P23", stock_qty=5, buy_qty=2
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-023", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    webhook_payload = {
        "id": "WH-EVT-023",
        "event_type": "CHECKOUT.PAYMENT-APPROVAL.REVERSED",
        "resource": {
            "id": "CAP-WH-023",
            "custom_id": order["id"],
        },
    }

    res = await async_client.post("/api/v1/payments/paypal/webhook", json=webhook_payload)
    assert res.status_code == 200

    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_24_webhook_idempotency_prevents_duplicate_processing(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 24: Re-delivering the exact same webhook event ID does not double-process."""
    seller = await create_user_helper(email="seller_p24@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p24@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="P24", stock_qty=10, buy_qty=2
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-024", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    webhook_payload = {
        "id": "WH-DUPLICATE-024",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAP-WH-024",
            "custom_id": order["id"],
            "status": "COMPLETED",
            "amount": {"value": order["total"], "currency_code": "USD"},
        },
    }

    # Delivery 1
    res1 = await async_client.post("/api/v1/payments/paypal/webhook", json=webhook_payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    # Delivery 2 (Duplicate)
    res2 = await async_client.post("/api/v1/payments/paypal/webhook", json=webhook_payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "ignored"

    # Stock is only finalized once (10 - 2 = 8, not 6!)
    inv_final = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_final.json()["quantity_on_hand"] == 8
    assert inv_final.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_25_webhook_invalid_payload_rejected(async_client: AsyncClient):
    """Test 25: Malformed webhook missing ID or event_type returns 400."""
    res = await async_client.post("/api/v1/payments/paypal/webhook", json={"data": "invalid"})
    assert res.status_code == 400


# ==============================================================================
# Order History & Security Tests (Tests 26 to 28)
# ==============================================================================

@pytest.mark.asyncio
async def test_26_order_history_includes_payment_status_and_provider(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 26: GET /api/v1/orders returns payment_status and payment_provider."""
    seller = await create_user_helper(email="seller_p26@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p26@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P26")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-026", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    res = await async_client.get("/api/v1/orders", headers=c_headers)
    assert res.status_code == 200
    orders_list = res.json()
    assert len(orders_list) >= 1
    target = next(o for o in orders_list if o["id"] == order["id"])
    assert target["payment_status"] == "PENDING"
    assert target["payment_provider"] == "PAYPAL"


@pytest.mark.asyncio
async def test_27_order_detail_includes_payment_status_and_provider(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 27: GET /api/v1/orders/{id} includes payment details and items snapshot."""
    seller = await create_user_helper(email="seller_p27@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p27@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, _ = await setup_customer_with_order(async_client, s_headers, c_headers, sku="P27")

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-027", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    res = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["order_number"] == order["order_number"]
    assert data["payment_status"] == "PENDING"
    assert data["payment_provider"] == "PAYPAL"
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_28_cannot_add_items_to_checked_out_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 28: Adding items after checkout targets the new active cart, checked-out cart remains immutable."""
    seller = await create_user_helper(email="seller_p28@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_p28@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="P28A", price="20.00", stock_qty=5)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="P28B", price="30.00", stock_qty=5)

    # Cart 1 has v1
    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 1}, headers=c_headers)
    await async_client.post("/api/v1/checkout", headers=c_headers)

    # Adding v2 goes to new active cart
    add_res = await async_client.post(
        "/api/v1/cart/items", json={"variant_id": v2, "quantity": 1}, headers=c_headers
    )
    assert add_res.status_code == 201
    cart_res = await async_client.get("/api/v1/cart", headers=c_headers)
    assert cart_res.status_code == 200
    assert len(cart_res.json()["items"]) == 1
    assert cart_res.json()["items"][0]["variant_id"] == v2
