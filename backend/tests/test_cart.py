import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.modules.catalog.enums import ProductStatus
from app.modules.users.enums import UserRole


# Helper fixture for creating active product, variant, and stock
async def create_catalog_item(
    async_client: AsyncClient,
    seller_headers: dict,
    sku: str = "CART-SKU-1",
    price: str = "49.99",
    stock_qty: int = 10,
    product_status: ProductStatus = ProductStatus.ACTIVE,
    product_is_active: bool = True,
    variant_is_active: bool = True,
) -> tuple[str, str]:
    """Helper to create a product and variant with initialized stock."""
    prod_payload = {
        "name": f"Fashion Product {sku}",
        "base_price": price,
        "status": product_status.value,
        "is_active": product_is_active,
    }
    prod_res = await async_client.post("/api/v1/products", json=prod_payload, headers=seller_headers)
    assert prod_res.status_code == 201
    product_id = prod_res.json()["id"]

    var_payload = {
        "sku": sku,
        "color": "Onyx Black",
        "size": "M",
        "price": price,
        "is_active": variant_is_active,
    }
    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json=var_payload,
        headers=seller_headers,
    )
    assert var_res.status_code == 201
    variant_id = var_res.json()["id"]

    if stock_qty > 0:
        adjust_res = await async_client.post(
            f"/api/v1/inventory/{variant_id}/adjust",
            json={"adjustment": stock_qty, "reason": "Initial stock for tests"},
            headers=seller_headers,
        )
        assert adjust_res.status_code == 200

    return product_id, variant_id


# ==============================================================================
# Cart Tests (Tests 1 to 14)
# ==============================================================================

@pytest.mark.asyncio
async def test_01_customer_gets_empty_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 1: Customer retrieves their active cart. An empty cart is auto-created if none exists."""
    customer = await create_user_helper(email="cust1@example.com", role=UserRole.CUSTOMER)
    headers = auth_headers_helper(customer)

    res = await async_client.get("/api/v1/cart", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == str(customer.id)
    assert data["status"] == "ACTIVE"
    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["item_count"] == 0


@pytest.mark.asyncio
async def test_02_customer_adds_item_to_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 2: Customer adds a valid purchasable variant to their active cart."""
    seller = await create_user_helper(email="seller_c2@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust2@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="ADD-02", price="35.00", stock_qty=5)

    add_res = await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 2},
        headers=c_headers,
    )
    assert add_res.status_code == 201
    data = add_res.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["variant_id"] == variant_id
    assert item["quantity"] == 2
    assert item["unit_price"] == "35.00"
    assert item["line_total"] == "70.00"
    assert item["sku"] == "ADD-02"
    assert data["subtotal"] == "70.00"
    assert data["item_count"] == 2


@pytest.mark.asyncio
async def test_03_adding_same_variant_increases_quantity(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 3: Adding an already existing variant increments quantity instead of creating duplicates."""
    seller = await create_user_helper(email="seller_c3@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust3@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="INCR-03", price="25.00", stock_qty=10)

    # Add 1 unit
    await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)
    # Add 3 more units of the same variant
    res2 = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 3}, headers=c_headers)

    assert res2.status_code == 201
    data = res2.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 4
    assert data["items"][0]["line_total"] == "100.00"
    assert data["subtotal"] == "100.00"
    assert data["item_count"] == 4


@pytest.mark.asyncio
async def test_04_customer_updates_item_quantity(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 4: Customer updates quantity of an existing item in their cart."""
    seller = await create_user_helper(email="seller_c4@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust4@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="UPD-04", price="50.00", stock_qty=10)
    add_res = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=c_headers)
    item_id = add_res.json()["items"][0]["id"]

    # Update quantity from 2 to 5
    patch_res = await async_client.patch(
        f"/api/v1/cart/items/{item_id}",
        json={"quantity": 5},
        headers=c_headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["items"][0]["quantity"] == 5
    assert data["items"][0]["line_total"] == "250.00"
    assert data["subtotal"] == "250.00"
    assert data["item_count"] == 5


@pytest.mark.asyncio
async def test_05_customer_removes_item(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 5: Customer deletes an item from their cart."""
    seller = await create_user_helper(email="seller_c5@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust5@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="REM-1", price="10.00", stock_qty=5)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="REM-2", price="20.00", stock_qty=5)

    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 1}, headers=c_headers)
    res = await async_client.post("/api/v1/cart/items", json={"variant_id": v2, "quantity": 2}, headers=c_headers)
    items = res.json()["items"]
    assert len(items) == 2
    item_to_delete = next(i for i in items if i["variant_id"] == v1)

    del_res = await async_client.delete(f"/api/v1/cart/items/{item_to_delete['id']}", headers=c_headers)
    assert del_res.status_code == 200
    data = del_res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["variant_id"] == v2
    assert data["subtotal"] == "40.00"


@pytest.mark.asyncio
async def test_06_customer_clears_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 6: Customer clears all items from cart; cart remains ACTIVE."""
    seller = await create_user_helper(email="seller_c6@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust6@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="CLR-1", price="15.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 2}, headers=c_headers)

    clear_res = await async_client.delete("/api/v1/cart", headers=c_headers)
    assert clear_res.status_code == 200
    data = clear_res.json()
    assert data["status"] == "ACTIVE"
    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["item_count"] == 0


@pytest.mark.asyncio
async def test_07_cannot_access_another_customer_cart(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 7: Carts are strictly isolated per customer; customers cannot see each other's carts."""
    seller = await create_user_helper(email="seller_c7@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust7a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust7b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    headers_a = auth_headers_helper(cust_a)
    headers_b = auth_headers_helper(cust_b)

    _, v = await create_catalog_item(async_client, s_headers, sku="ISO-7", price="25.00", stock_qty=5)
    await async_client.post("/api/v1/cart/items", json={"variant_id": v, "quantity": 2}, headers=headers_a)

    cart_b = await async_client.get("/api/v1/cart", headers=headers_b)
    assert cart_b.status_code == 200
    assert cart_b.json()["items"] == []
    assert cart_b.json()["customer_id"] == str(cust_b.id)


@pytest.mark.asyncio
async def test_08_cannot_modify_another_customer_cart_item(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 8: Customer B cannot update or delete Customer A's cart item (returns 404)."""
    seller = await create_user_helper(email="seller_c8@example.com", role=UserRole.SELLER)
    cust_a = await create_user_helper(email="cust8a@example.com", role=UserRole.CUSTOMER)
    cust_b = await create_user_helper(email="cust8b@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    headers_a = auth_headers_helper(cust_a)
    headers_b = auth_headers_helper(cust_b)

    _, v = await create_catalog_item(async_client, s_headers, sku="MOD-8", price="30.00", stock_qty=5)
    res_a = await async_client.post("/api/v1/cart/items", json={"variant_id": v, "quantity": 1}, headers=headers_a)
    item_id = res_a.json()["items"][0]["id"]

    # Customer B attempts to modify Customer A's item
    patch_res = await async_client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 3}, headers=headers_b)
    assert patch_res.status_code == 404

    # Customer B attempts to delete Customer A's item
    del_res = await async_client.delete(f"/api/v1/cart/items/{item_id}", headers=headers_b)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_09_cannot_add_inactive_variant(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 9: Attempting to add an inactive variant returns 400 Bad Request."""
    seller = await create_user_helper(email="seller_c9@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust9@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(
        async_client, s_headers, sku="INACT-VAR-9", price="20.00", stock_qty=5, variant_is_active=False
    )

    res = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)
    assert res.status_code == 400
    assert "not active" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_10_cannot_add_draft_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 10: Attempting to add a variant belonging to a DRAFT product returns 400 Bad Request."""
    seller = await create_user_helper(email="seller_c10@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust10@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(
        async_client, s_headers, sku="DRAFT-10", price="20.00", stock_qty=5, product_status=ProductStatus.DRAFT
    )

    res = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)
    assert res.status_code == 400
    assert "not available" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_11_cannot_add_archived_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 11: Attempting to add a variant belonging to an ARCHIVED product returns 400 Bad Request."""
    seller = await create_user_helper(email="seller_c11@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust11@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(
        async_client, s_headers, sku="ARCH-11", price="20.00", stock_qty=5, product_status=ProductStatus.ARCHIVED
    )

    res = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=c_headers)
    assert res.status_code == 400
    assert "not available" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_12_cannot_exceed_available_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 12: Adding or updating to a quantity greater than available stock returns 400 Bad Request."""
    seller = await create_user_helper(email="seller_c12@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust12@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, variant_id = await create_catalog_item(async_client, s_headers, sku="STOCK-12", price="20.00", stock_qty=3)

    # 1. Attempt to add 4 units when only 3 exist
    res_add = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 4}, headers=c_headers)
    assert res_add.status_code == 400
    assert "exceeds available stock" in res_add.json()["detail"]

    # 2. Add 2 units (valid)
    res_ok = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=c_headers)
    assert res_ok.status_code == 201
    item_id = res_ok.json()["items"][0]["id"]

    # 3. Attempt to add 2 more units (2 + 2 = 4 > 3)
    res_add_more = await async_client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=c_headers)
    assert res_add_more.status_code == 400

    # 4. Attempt to update quantity directly to 5 > 3
    res_patch = await async_client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 5}, headers=c_headers)
    assert res_patch.status_code == 400


@pytest.mark.asyncio
async def test_13_correct_subtotal_calculation(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 13: Subtotal accurately equals the sum of line totals across multiple distinct variants."""
    seller = await create_user_helper(email="seller_c13@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust13@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="CALC-1", price="19.99", stock_qty=10)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="CALC-2", price="34.50", stock_qty=10)
    _, v3 = await create_catalog_item(async_client, s_headers, sku="CALC-3", price="100.00", stock_qty=10)

    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 2}, headers=c_headers)  # 39.98
    await async_client.post("/api/v1/cart/items", json={"variant_id": v2, "quantity": 1}, headers=c_headers)  # 34.50
    res = await async_client.post("/api/v1/cart/items", json={"variant_id": v3, "quantity": 3}, headers=c_headers)  # 300.00

    data = res.json()
    assert data["subtotal"] == "374.48"
    assert data["item_count"] == 6


@pytest.mark.asyncio
async def test_14_money_calculations_use_decimal_safely(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 14: Verifies precision is retained without binary floating-point roundoff errors (e.g. 0.1 + 0.2)."""
    seller = await create_user_helper(email="seller_c14@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust14@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    _, v1 = await create_catalog_item(async_client, s_headers, sku="DEC-1", price="0.10", stock_qty=10)
    _, v2 = await create_catalog_item(async_client, s_headers, sku="DEC-2", price="0.20", stock_qty=10)

    await async_client.post("/api/v1/cart/items", json={"variant_id": v1, "quantity": 1}, headers=c_headers)
    res = await async_client.post("/api/v1/cart/items", json={"variant_id": v2, "quantity": 1}, headers=c_headers)

    data = res.json()
    assert data["subtotal"] == "0.30"  # Exact Decimal, not 0.30000000000000004
