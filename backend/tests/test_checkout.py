import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.models import Cart
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.orders.models import Order
from app.modules.users.enums import UserRole
from tests.test_cart import create_catalog_item


# ==============================================================================
# Checkout Tests (Tests 15 to 27)
# ==============================================================================

@pytest.mark.asyncio
async def test_15_empty_cart_checkout_rejected(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 15: Attempting to checkout with an empty cart returns 400 Bad Request."""
    customer = await create_user_helper(email="cust15@example.com", role=UserRole.CUSTOMER)
    headers = auth_headers_helper(customer)

    # Empty cart
    res = await async_client.post("/api/v1/checkout", headers=headers)
    assert res.status_code == 400
    assert "empty cart" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_16_successful_checkout_creates_order(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 16: Checkout successfully creates an Order with status PENDING_PAYMENT."""
    seller = await create_user_helper(email="seller16@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust16@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="CHK-16", price="80.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=c_headers)

    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 201
    order = res.json()
    assert order["customer_id"] == str(customer.id)
    assert order["status"] == "PENDING_PAYMENT"
    assert order["order_number"].startswith("ORD-")
    assert order["subtotal"] == "160.00"
    assert order["total"] == "160.00"
    assert len(order["items"]) == 1


@pytest.mark.asyncio
async def test_17_correct_order_items_created(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 17: Order items are created accurately matching each cart line item."""
    seller = await create_user_helper(email="seller17@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust17@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="ITEM-17A", price="25.00", stock_qty=10)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="ITEM-17B", price="45.00", stock_qty=10)

    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 2}, headers=c_headers)
    await async_client.post("/api/v1/cart/items", json={"variant_id": v2, "quantity": 1}, headers=c_headers)

    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 201
    order = res.json()
    assert len(order["items"]) == 2
    item_a = next(i for i in order["items"] if i["variant_id"] == v1)
    item_b = next(i for i in order["items"] if i["variant_id"] == v2)
    assert item_a["quantity"] == 2
    assert item_a["line_total"] == "50.00"
    assert item_b["quantity"] == 1
    assert item_b["line_total"] == "45.00"
    assert order["total"] == "95.00"


@pytest.mark.asyncio
async def test_18_order_item_historical_snapshots_stored(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 18: Product name, SKU, and unit price are saved as historical snapshots on order items."""
    seller = await create_user_helper(email="seller18@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust18@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="SNAP-18", price="120.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)

    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 201
    item = res.json()["items"][0]
    assert item["sku"] == "SNAP-18"
    assert "Fashion Product SNAP-18" in item["product_name"]
    assert item["unit_price"] == "120.00"


@pytest.mark.asyncio
async def test_19_inventory_decreases_correctly(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 19: Physical inventory decreases by exactly the purchased quantity upon checkout."""
    seller = await create_user_helper(email="seller19@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust19@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="DEC-19", price="30.00", stock_qty=10)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 4}, headers=c_headers)

    # Checkout 4 units
    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 201

    # Verify inventory is now 10 - 4 = 6
    inv_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_res.json()["quantity_on_hand"] == 6
    assert inv_res.json()["quantity_available"] == 6


@pytest.mark.asyncio
async def test_20_cart_becomes_checked_out(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 20: Cart status transitions to CHECKED_OUT and subsequent GET /cart yields a new empty ACTIVE cart."""
    seller = await create_user_helper(email="seller20@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust20@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="STAT-20", price="40.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)

    checkout_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert checkout_res.status_code == 201

    # Next fetch of cart returns a brand new empty ACTIVE cart
    new_cart_res = await async_client.get("/api/v1/cart", headers=c_headers)
    assert new_cart_res.status_code == 200
    assert new_cart_res.json()["status"] == "ACTIVE"
    assert new_cart_res.json()["items"] == []


@pytest.mark.asyncio
async def test_21_order_starts_pending_payment(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 21: Created order status is explicitly PENDING_PAYMENT."""
    seller = await create_user_helper(email="seller21@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust21@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="PEND-21", price="55.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)

    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 201
    assert res.json()["status"] == "PENDING_PAYMENT"


@pytest.mark.asyncio
async def test_22_insufficient_stock_causes_rollback(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 22: If stock is reduced between cart addition and checkout, checkout is rejected and rolls back."""
    seller = await create_user_helper(email="seller22@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust22@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="ROLL-22", price="60.00", stock_qty=5)

    # Customer adds 4 units
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 4}, headers=c_headers)

    # Seller adjusts stock down by -3, leaving only 2 units available
    adj_res = await async_client.post(
        f"/api/v1/inventory/{variant_id}/adjust",
        json={"adjustment": -3, "reason": "Damage"},
        headers=s_headers,
    )
    assert adj_res.status_code == 200

    # Checkout fails with 400
    chk_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert chk_res.status_code == 400
    assert "insufficient stock" in chk_res.json()["detail"].lower()

    # Verify inventory was NOT changed by the failed checkout (still 2)
    inv_check = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv_check.json()["quantity_on_hand"] == 2

    # Cart remains ACTIVE with the 4 items
    cart_check = await async_client.get("/api/v1/cart", headers=c_headers)
    assert cart_check.json()["status"] == "ACTIVE"
    assert len(cart_check.json()["items"]) == 1


@pytest.mark.asyncio
async def test_23_failed_checkout_does_not_partially_create_order(
    async_client: AsyncClient, db_session: AsyncSession, create_user_helper, auth_headers_helper
):
    """Test 23: Failed checkout does not leave orphan partial orders in the database."""
    seller = await create_user_helper(email="seller23@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust23@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="MULTI-23A", price="10.00", stock_qty=5)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="MULTI-23B", price="20.00", stock_qty=1)

    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 2}, headers=c_headers)
    await async_client.post("/api/v1/cart/items", json={"variant_id": v2, "quantity": 1}, headers=c_headers)

    # Deplete v2 stock before checkout
    await async_client.post(
        f"/api/v1/inventory/{v2}/adjust",
        json={"adjustment": -1, "reason": "Sold in store"},
        headers=s_headers,
    )

    # Checkout fails on v2
    res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert res.status_code == 400

    # Verify 0 orders exist for this customer
    orders_res = await async_client.get("/api/v1/orders", headers=c_headers)
    assert orders_res.status_code == 200
    assert len(orders_res.json()) == 0


@pytest.mark.asyncio
async def test_24_customer_cannot_checkout_another_customer_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 24: Customer B checking out only checks out their own active cart, never Customer A's."""
    seller = await create_user_helper(email="seller24@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust24a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust24b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    headers_a = auth_headers_helper(cust_a)
    headers_b = auth_headers_helper(cust_b)

    _, v = await create_catalog_item(async_client, s_headers, sku="ISO-24", price="50.00", stock_qty=10)
    await async_client.post("/api/v1/cart/items", json={"variant_id": v, "quantity": 1}, headers=headers_a)

    # Customer B attempts checkout with empty cart
    res_b = await async_client.post("/api/v1/checkout", headers=headers_b)
    assert res_b.status_code == 400

    # Customer A's cart is still ACTIVE
    cart_a = await async_client.get("/api/v1/cart", headers=headers_a)
    assert cart_a.json()["status"] == "ACTIVE"
    assert len(cart_a.json()["items"]) == 1


@pytest.mark.asyncio
async def test_25_inactive_draft_archived_product_cannot_checkout(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 25: If product status becomes ARCHIVED or DRAFT after adding to cart, checkout is blocked."""
    seller = await create_user_helper(email="seller25@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust25@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    prod_id, variant_id = await create_catalog_item(async_client, s_headers, sku="BLOCKED-25", price="30.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)

    # Seller archives product
    patch_prod = await async_client.patch(f"/api/v1/products/{prod_id}", json={"status": "ARCHIVED"}, headers=s_headers)
    assert patch_prod.status_code == 200

    # Checkout is rejected
    chk_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert chk_res.status_code == 400
    assert "no longer available" in chk_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_26_price_changes_between_cart_and_checkout_use_authoritative_price(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 26: If variant price changes after adding to cart, checkout charges current authoritative price."""
    seller = await create_user_helper(email="seller26@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust26@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    prod_id, variant_id = await create_catalog_item(async_client, s_headers, sku="PRICE-26", price="50.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=c_headers)

    # Seller updates variant price from 50.00 to 65.00
    patch_var = await async_client.patch(
        f"/api/v1/products/{prod_id}/variants/{variant_id}",
        json={"price": "65.00"},
        headers=s_headers,
    )
    assert patch_var.status_code == 200

    # Checkout uses authoritative price 65.00 * 2 = 130.00
    chk_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert chk_res.status_code == 201
    order = chk_res.json()
    assert order["subtotal"] == "130.00"
    assert order["total"] == "130.00"
    assert order["items"][0]["unit_price"] == "65.00"
    assert order["items"][0]["line_total"] == "130.00"


@pytest.mark.asyncio
async def test_27_checkout_preserves_historical_order_snapshots(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 27: Modifying or deleting product/variant after checkout does not alter historical order snapshot."""
    seller = await create_user_helper(email="seller27@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust27@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    prod_id, variant_id = await create_catalog_item(async_client, s_headers, sku="HIST-27", price="75.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)

    chk_res = await async_client.post("/api/v1/checkout", headers=c_headers)
    assert chk_res.status_code == 201
    order_id = chk_res.json()["id"]

    # Seller updates product name and variant SKU
    await async_client.patch(f"/api/v1/products/{prod_id}", json={"name": "Renamed Future Product"}, headers=s_headers)
    await async_client.patch(f"/api/v1/products/{prod_id}/variants/{variant_id}", json={"sku": "HIST-27-NEW"}, headers=s_headers)

    # Customer fetches historic order: snapshot remains immutable
    order_res = await async_client.get(f"/api/v1/orders/{order_id}", headers=c_headers)
    assert order_res.status_code == 200
    item = order_res.json()["items"][0]
    assert item["sku"] == "HIST-27"
    assert "Fashion Product HIST-27" in item["product_name"]
    assert item["unit_price"] == "75.00"
