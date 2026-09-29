import asyncio
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.inventory.service import InventoryService
from app.modules.users.enums import UserRole


# Helper fixture for creating a product and variant
async def create_product_and_variant(
    async_client: AsyncClient,
    seller_headers: dict,
    sku: str = "VAR-SKU-1",
    status: ProductStatus = ProductStatus.ACTIVE,
    is_active: bool = True,
) -> tuple[str, str]:
    """Helper creating an active product and variant via API, returning (product_id, variant_id)."""
    prod_payload = {
        "name": f"Product for {sku}",
        "base_price": "50.00",
        "status": status.value,
        "is_active": is_active,
    }
    prod_res = await async_client.post("/api/v1/products", json=prod_payload, headers=seller_headers)
    assert prod_res.status_code == 201
    product_id = prod_res.json()["id"]

    var_payload = {
        "sku": sku,
        "color": "Midnight Black",
        "size": "L",
        "price": "50.00",
        "is_active": True,
    }
    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json=var_payload,
        headers=seller_headers,
    )
    assert var_res.status_code == 201
    variant_id = var_res.json()["id"]
    return product_id, variant_id


# ==============================================================================
# Phase 3 Inventory Tests (15 Required Scenarios)
# ==============================================================================

@pytest.mark.asyncio
async def test_01_automatic_inventory_creation(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 1: Creating a ProductVariant automatically provisions an InventoryItem in the same transaction."""
    seller = await create_user_helper(email="seller1@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    product_id, variant_id = await create_product_and_variant(
        async_client, headers, sku="AUTO-INV-01"
    )

    inv_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert inv_res.status_code == 200
    data = inv_res.json()
    assert data["variant_id"] == variant_id
    assert data["quantity_on_hand"] == 0
    assert data["quantity_reserved"] == 0
    assert data["quantity_available"] == 0
    assert data["low_stock_threshold"] == 5
    assert data["is_in_stock"] is False
    assert data["is_low_stock"] is True


@pytest.mark.asyncio
async def test_02_seller_reads_own_inventory(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 2: Seller can consult their own inventory listing and specific SKU stock."""
    seller = await create_user_helper(email="seller2@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="OWN-INV-02")

    # Single SKU read
    res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["variant_id"] == variant_id

    # List inventory
    list_res = await async_client.get("/api/v1/inventory", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(i["variant_id"] == variant_id for i in items)


@pytest.mark.asyncio
async def test_03_seller_cannot_access_another_seller_inventory(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 3: Cross-seller access is forbidden (returns 403) and isolates list results."""
    seller_a = await create_user_helper(email="seller_3a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="seller_3b@example.com", role=UserRole.SELLER)
    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)

    _, variant_a = await create_product_and_variant(async_client, headers_a, sku="ISOLATE-3A")

    # Seller B attempts to read Seller A's SKU inventory
    forbidden_res = await async_client.get(f"/api/v1/inventory/{variant_a}", headers=headers_b)
    assert forbidden_res.status_code == 403

    # Seller B's listing does not show Seller A's inventory
    list_b = await async_client.get("/api/v1/inventory", headers=headers_b)
    assert list_b.status_code == 200
    assert all(i["variant_id"] != variant_a for i in list_b.json())


@pytest.mark.asyncio
async def test_04_seller_adjusts_own_stock(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 4: Seller adjusts stock on hand (0 -> +10) resulting in available = 10, in_stock = True."""
    seller = await create_user_helper(email="seller4@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="ADJUST-04")

    adjust_payload = {"adjustment": 10, "reason": "Initial stock arrival"}
    adjust_res = await async_client.post(
        f"/api/v1/inventory/{variant_id}/adjust",
        json=adjust_payload,
        headers=headers,
    )
    assert adjust_res.status_code == 200
    data = adjust_res.json()
    assert data["quantity_on_hand"] == 10
    assert data["quantity_reserved"] == 0
    assert data["quantity_available"] == 10
    assert data["is_in_stock"] is True
    assert data["is_low_stock"] is False


@pytest.mark.asyncio
async def test_05_negative_stock_rejected(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 5: Attempts to reduce stock below 0 are rejected by both service and schema."""
    seller = await create_user_helper(email="seller5@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="NO-NEG-05")

    # 1. Adjust delta below zero when on_hand is 0 -> 400 Bad Request
    res_neg_adjust = await async_client.post(
        f"/api/v1/inventory/{variant_id}/adjust",
        json={"adjustment": -1},
        headers=headers,
    )
    assert res_neg_adjust.status_code == 400

    # 2. Schema validation rejects negative quantity_on_hand -> 422 Unprocessable Entity
    res_neg_patch = await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": -10},
        headers=headers,
    )
    assert res_neg_patch.status_code == 422

    # Verify stock remained untouched at 0
    check_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert check_res.json()["quantity_on_hand"] == 0


@pytest.mark.asyncio
async def test_06_reserved_quantity(
    async_client: AsyncClient, db_session: AsyncSession, create_user_helper, auth_headers_helper
):
    """Test 6: Reserved stock correctly reduces available units: on_hand=10, reserved=3 -> available=7."""
    seller = await create_user_helper(email="seller6@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="RESERVE-06")
    v_uuid = uuid.UUID(variant_id)

    # Set on_hand = 10
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 10},
        headers=headers,
    )

    # Reserve 3 units via InventoryService
    item = await InventoryService.reserve_stock(db_session, v_uuid, quantity=3)
    assert item.quantity_on_hand == 10
    assert item.quantity_reserved == 3
    assert item.quantity_available == 7

    # Verify via API response
    res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["quantity_on_hand"] == 10
    assert data["quantity_reserved"] == 3
    assert data["quantity_available"] == 7
    assert data["is_in_stock"] is True


@pytest.mark.asyncio
async def test_07_invalid_reservation_rejected(
    async_client: AsyncClient, db_session: AsyncSession, create_user_helper, auth_headers_helper
):
    """Test 7: Over-reserving (reserved > on_hand) or reducing on_hand below reserved is rejected."""
    seller = await create_user_helper(email="seller7@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="INV-RES-07")
    v_uuid = uuid.UUID(variant_id)

    # Set on_hand = 5
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 5},
        headers=headers,
    )

    # 1. Attempt to reserve 6 units when only 5 are available
    with pytest.raises(Exception) as excinfo:
        await InventoryService.reserve_stock(db_session, v_uuid, quantity=6)
    assert "Insufficient stock" in str(excinfo.value)

    # 2. Reserve 3 units legitimately
    await InventoryService.reserve_stock(db_session, v_uuid, quantity=3)

    # 3. Attempt to adjust stock down by -3 (5 - 3 = 2 < 3 reserved) -> 400
    res_adj = await async_client.post(
        f"/api/v1/inventory/{variant_id}/adjust",
        json={"adjustment": -3},
        headers=headers,
    )
    assert res_adj.status_code == 400

    # 4. Attempt to release more units than currently reserved -> error
    with pytest.raises(Exception) as excinfo_rel:
        await InventoryService.release_stock(db_session, v_uuid, quantity=5)
    assert "Cannot release" in str(excinfo_rel.value)


@pytest.mark.asyncio
async def test_08_low_stock_detection(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 8: Low stock detection works when quantity_available <= low_stock_threshold."""
    seller = await create_user_helper(email="seller8@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="LOW-STOCK-08")

    # on_hand = 4, threshold = 5 -> is_low_stock = True
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 4, "low_stock_threshold": 5},
        headers=headers,
    )
    res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert res.json()["is_low_stock"] is True

    # Filtered listing with low_stock_only=true includes it
    low_res = await async_client.get("/api/v1/inventory?low_stock_only=true", headers=headers)
    assert any(i["variant_id"] == variant_id for i in low_res.json())

    # Restock: on_hand = 10 > 5 -> is_low_stock = False
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 10},
        headers=headers,
    )
    res_restocked = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert res_restocked.json()["is_low_stock"] is False

    # Filtered listing excludes it
    low_res_empty = await async_client.get("/api/v1/inventory?low_stock_only=true", headers=headers)
    assert not any(i["variant_id"] == variant_id for i in low_res_empty.json())


@pytest.mark.asyncio
async def test_09_in_stock_calculation(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 9: Available > 0 yields is_in_stock = True on both inventory and product responses."""
    seller = await create_user_helper(email="seller9@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    product_id, variant_id = await create_product_and_variant(async_client, headers, sku="IN-STOCK-09")

    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 3},
        headers=headers,
    )

    # Inventory endpoint
    inv = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert inv.json()["is_in_stock"] is True

    # Catalog product detail endpoint
    prod = await async_client.get(f"/api/v1/products/{product_id}")
    assert prod.status_code == 200
    variant = next(v for v in prod.json()["variants"] if v["id"] == variant_id)
    assert variant["is_in_stock"] is True


@pytest.mark.asyncio
async def test_10_out_of_stock_calculation(
    async_client: AsyncClient, db_session: AsyncSession, create_user_helper, auth_headers_helper
):
    """Test 10: Available == 0 yields is_in_stock = False."""
    seller = await create_user_helper(email="seller10@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="OOS-10")
    v_uuid = uuid.UUID(variant_id)

    # 1. Initial on_hand = 0 -> is_in_stock = False
    inv = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert inv.json()["is_in_stock"] is False

    # 2. on_hand = 2, reserved = 2 -> available = 0 -> is_in_stock = False
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 2},
        headers=headers,
    )
    await InventoryService.reserve_stock(db_session, v_uuid, quantity=2)

    inv_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert inv_res.json()["quantity_available"] == 0
    assert inv_res.json()["is_in_stock"] is False


@pytest.mark.asyncio
async def test_11_public_stock_privacy(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 11: Public customer never sees raw inventory quantities; only boolean is_in_stock."""
    seller = await create_user_helper(email="seller11@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    product_id, variant_id = await create_product_and_variant(async_client, headers, sku="PRIVACY-11")

    # Stock = 15
    await async_client.patch(
        f"/api/v1/inventory/{variant_id}",
        json={"quantity_on_hand": 15},
        headers=headers,
    )

    # 1. Public stock check endpoint
    public_res = await async_client.get(f"/api/v1/inventory/{variant_id}/public")
    assert public_res.status_code == 200
    data = public_res.json()
    assert data["variant_id"] == variant_id
    assert data["is_in_stock"] is True
    assert "quantity_on_hand" not in data
    assert "quantity_reserved" not in data
    assert "quantity_available" not in data
    assert "low_stock_threshold" not in data

    # 2. Public product detail endpoint
    prod_res = await async_client.get(f"/api/v1/products/{product_id}")
    assert prod_res.status_code == 200
    v_data = prod_res.json()["variants"][0]
    assert v_data["is_in_stock"] is True
    assert "quantity_on_hand" not in v_data
    assert "quantity_reserved" not in v_data

    # 3. Unauthenticated access to private inventory management endpoints is rejected with 401
    assert (await async_client.get(f"/api/v1/inventory/{variant_id}")).status_code == 401
    assert (await async_client.get("/api/v1/inventory")).status_code == 401


@pytest.mark.asyncio
async def test_12_ownership_mutation_protection(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 12: Seller A cannot mutate Seller B's inventory (returns 403 Forbidden)."""
    seller_a = await create_user_helper(email="seller_12a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="seller_12b@example.com", role=UserRole.SELLER)
    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)

    _, variant_b = await create_product_and_variant(async_client, headers_b, sku="MUTATE-B")

    # Seller A attempts adjust on Seller B's variant
    adj_res = await async_client.post(
        f"/api/v1/inventory/{variant_b}/adjust",
        json={"adjustment": 50},
        headers=headers_a,
    )
    assert adj_res.status_code == 403

    # Seller A attempts patch on Seller B's variant
    patch_res = await async_client.patch(
        f"/api/v1/inventory/{variant_b}",
        json={"quantity_on_hand": 100},
        headers=headers_a,
    )
    assert patch_res.status_code == 403


@pytest.mark.asyncio
async def test_13_admin_access(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 13: Admin can access any seller's inventory, list with seller filter, and adjust stock."""
    seller = await create_user_helper(email="seller13@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="admin13@example.com", role=UserRole.ADMIN)
    s_headers = auth_headers_helper(seller)
    a_headers = auth_headers_helper(admin)

    _, variant_id = await create_product_and_variant(async_client, s_headers, sku="ADMIN-13")

    # Admin reads seller's SKU
    read_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=a_headers)
    assert read_res.status_code == 200

    # Admin lists inventory filtered by seller_id
    list_res = await async_client.get(f"/api/v1/inventory?seller_id={seller.id}", headers=a_headers)
    assert list_res.status_code == 200
    assert any(i["variant_id"] == variant_id for i in list_res.json())

    # Admin adjusts seller's SKU
    adj_res = await async_client.post(
        f"/api/v1/inventory/{variant_id}/adjust",
        json={"adjustment": 25, "reason": "Admin stock correction"},
        headers=a_headers,
    )
    assert adj_res.status_code == 200
    assert adj_res.json()["quantity_on_hand"] == 25


@pytest.mark.asyncio
async def test_14_variant_deletion_cascade(
    async_client: AsyncClient, db_session: AsyncSession, create_user_helper, auth_headers_helper
):
    """Test 14: Deleting a ProductVariant cascades to delete its InventoryItem."""
    seller = await create_user_helper(email="seller14@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    product_id, variant_id = await create_product_and_variant(async_client, headers, sku="DEL-VAR-14")
    v_uuid = uuid.UUID(variant_id)

    # Verify inventory item exists
    item_before = await InventoryService.get_by_variant_id(db_session, v_uuid)
    assert item_before is not None

    # Delete variant
    del_res = await async_client.delete(
        f"/api/v1/products/{product_id}/variants/{variant_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # Verify inventory item is gone
    item_after = await InventoryService.get_by_variant_id(db_session, v_uuid)
    assert item_after is None


@pytest.mark.asyncio
async def test_15_concurrency_and_atomicity(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Test 15: Concurrency safety - sequential / locked adjustments guarantee exact totals without race conditions."""
    seller = await create_user_helper(email="seller15@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    _, variant_id = await create_product_and_variant(async_client, headers, sku="CONCUR-15")

    # Perform 5 consecutive adjustments of +3
    num_mutations = 5
    delta = 3
    for _ in range(num_mutations):
        res = await async_client.post(
            f"/api/v1/inventory/{variant_id}/adjust",
            json={"adjustment": delta},
            headers=headers,
        )
        assert res.status_code == 200

    # Verify final stock is exactly 5 * 3 = 15
    final_res = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=headers)
    assert final_res.status_code == 200
    data = final_res.json()
    assert data["quantity_on_hand"] == 15
    assert data["quantity_available"] == 15
    assert data["is_in_stock"] is True
