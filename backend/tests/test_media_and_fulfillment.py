import io
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.storage import StorageService, validate_image_file
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.catalog.models import Product, ProductVariant, Category, Brand
from app.modules.catalog.enums import ProductStatus
from app.modules.inventory.models import InventoryItem
from app.modules.orders.models import Order, OrderItem, SubOrder
from app.modules.orders.enums import OrderStatus


# Minimal valid file bytes with real magic signatures
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 100
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 100
VALID_WEBP_BYTES = b"RIFF\x20\x00\x00\x00WEBPVP8 " + b"\x00" * 100


# --- Unit Tests for Storage Validation ---

def test_validate_image_file_valid_jpeg():
    ext = validate_image_file(VALID_JPEG_BYTES, "test.jpg", "image/jpeg")
    assert ext == ".jpg"


def test_validate_image_file_valid_png():
    ext = validate_image_file(VALID_PNG_BYTES, "photo.png", "image/png")
    assert ext == ".png"


def test_validate_image_file_valid_webp():
    ext = validate_image_file(VALID_WEBP_BYTES, "banner.webp", "image/webp")
    assert ext == ".webp"


def test_validate_image_file_empty():
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(b"", "empty.jpg", "image/jpeg")
    assert "empty" in str(exc_info.value.detail).lower()


def test_validate_image_file_oversized():
    oversized = b"\xff\xd8\xff\xe0" + b"\x00" * (10 * 1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(oversized, "huge.jpg", "image/jpeg")
    assert "exceeds" in str(exc_info.value.detail).lower()


def test_validate_image_file_invalid_mime():
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(b"hello world text", "text.txt", "text/plain")
    assert "unsupported" in str(exc_info.value.detail).lower()


def test_validate_image_file_spoofed_magic_bytes():
    fake_jpeg = b"This is not a real JPEG image file at all"
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(fake_jpeg, "fake.jpg", "image/jpeg")
    assert "does not match" in str(exc_info.value.detail).lower()


# --- Fixtures for Catalog & Multi-Vendor Setup ---

@pytest.fixture
async def seller_one(create_user_helper) -> User:
    return await create_user_helper(
        email="seller1@fashion.local",
        role=UserRole.SELLER,
        first_name="Seller",
        last_name="One",
    )


@pytest.fixture
async def seller_two(create_user_helper) -> User:
    return await create_user_helper(
        email="seller2@fashion.local",
        role=UserRole.SELLER,
        first_name="Seller",
        last_name="Two",
    )


@pytest.fixture
async def customer_user(create_user_helper) -> User:
    return await create_user_helper(
        email="customer@fashion.local",
        role=UserRole.CUSTOMER,
        first_name="Alice",
        last_name="Customer",
    )


@pytest.fixture
async def admin_user(create_user_helper) -> User:
    return await create_user_helper(
        email="admin@fashion.local",
        role=UserRole.ADMIN,
        first_name="Super",
        last_name="Admin",
    )


@pytest.fixture
async def default_catalog(db_session: AsyncSession, seller_one: User, seller_two: User):
    cat = Category(name="Apparel", slug="apparel")
    brand = Brand(name="FashionCorp", slug="fashioncorp")
    db_session.add_all([cat, brand])
    await db_session.commit()
    await db_session.refresh(cat)
    await db_session.refresh(brand)

    # Product 1 belonging to seller_one
    p1 = Product(
        name="Silk Blouse",
        slug="silk-blouse",
        base_price=95.0,
        seller_id=seller_one.id,
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE,
        is_active=True,
    )
    # Product 2 belonging to seller_two
    p2 = Product(
        name="Leather Boots",
        slug="leather-boots",
        base_price=180.0,
        seller_id=seller_two.id,
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE,
        is_active=True,
    )
    db_session.add_all([p1, p2])
    await db_session.commit()
    await db_session.refresh(p1)
    await db_session.refresh(p2)

    # Variants
    v1 = ProductVariant(
        product_id=p1.id,
        sku="SILK-BLOUSE-S",
        price=95.0,
        is_active=True,
    )
    v2 = ProductVariant(
        product_id=p2.id,
        sku="BOOTS-BLK-42",
        price=180.0,
        is_active=True,
    )
    db_session.add_all([v1, v2])
    await db_session.commit()
    await db_session.refresh(v1)
    await db_session.refresh(v2)

    # Inventory
    inv1 = InventoryItem(variant_id=v1.id, quantity_on_hand=50, quantity_reserved=0)
    inv2 = InventoryItem(variant_id=v2.id, quantity_on_hand=30, quantity_reserved=0)
    db_session.add_all([inv1, inv2])
    await db_session.commit()

    return {"p1": p1, "p2": p2, "v1": v1, "v2": v2, "category": cat, "brand": brand}


# --- Media API Endpoints Tests ---

@pytest.mark.anyio
async def test_seller_can_upload_media_to_own_product(
    async_client: AsyncClient,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
    monkeypatch,
):
    def mock_upload(cls, data, object_key, content_type="application/octet-stream"):
        return f"http://localhost:9000/fashion-media/{object_key}"

    monkeypatch.setattr(StorageService, "upload_file", classmethod(mock_upload))

    p1_id = str(default_catalog["p1"].id)
    headers = auth_headers_helper(seller_one)

    files = {"file": ("blouse.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = await async_client.post(
        f"/api/v1/products/{p1_id}/media/upload",
        headers=headers,
        files=files,
        data={"is_primary": "true"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == p1_id
    assert data["is_primary"] is True
    assert data["mime_type"] == "image/jpeg"
    assert data["original_filename"] == "blouse.jpg"
    assert "url" in data
    assert "fashion-media" in data["url"]


@pytest.mark.anyio
async def test_seller_cannot_upload_media_to_other_seller_product(
    async_client: AsyncClient,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    p2_id = str(default_catalog["p2"].id)
    headers = auth_headers_helper(seller_one)

    files = {"file": ("hack.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = await async_client.post(
        f"/api/v1/products/{p2_id}/media/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_customer_cannot_upload_media(
    async_client: AsyncClient,
    customer_user: User,
    default_catalog: dict,
    auth_headers_helper,
):
    p1_id = str(default_catalog["p1"].id)
    headers = auth_headers_helper(customer_user)

    files = {"file": ("pic.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = await async_client.post(
        f"/api/v1/products/{p1_id}/media/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_upload_rejects_invalid_file_format(
    async_client: AsyncClient,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    p1_id = str(default_catalog["p1"].id)
    headers = auth_headers_helper(seller_one)

    files = {"file": ("script.sh", io.BytesIO(b"#!/bin/bash\necho bad"), "text/plain")}
    response = await async_client.post(
        f"/api/v1/products/{p1_id}/media/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_upload_rejects_spoofed_content(
    async_client: AsyncClient,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    p1_id = str(default_catalog["p1"].id)
    headers = auth_headers_helper(seller_one)

    # Declares image/png but sends text
    files = {"file": ("malicious.png", io.BytesIO(b"Just plain text string"), "image/png")}
    response = await async_client.post(
        f"/api/v1/products/{p1_id}/media/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"].lower()


# --- Multi-Vendor Checkout Split & SubOrders Tests ---

@pytest.mark.anyio
async def test_single_seller_cart_checkout_creates_one_sub_order(
    async_client: AsyncClient,
    customer_user: User,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    s1_id = str(seller_one.id)
    headers = auth_headers_helper(customer_user)

    # Add 2 items via Cart API
    cart_res = await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 2},
        headers=headers,
    )
    assert cart_res.status_code == 201

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers)
    assert checkout_res.status_code == 201
    data = checkout_res.json()

    assert Decimal(str(data["total"])) == Decimal("190.00")
    assert len(data["sub_orders"]) == 1
    sub = data["sub_orders"][0]
    assert sub["seller_id"] == s1_id
    assert sub["status"] == "PENDING_PAYMENT"
    assert Decimal(str(sub["total"])) == Decimal("190.00")

    # Verify OrderItem snapshot contains sub_order_id and seller_id
    item = data["items"][0]
    assert item["seller_id"] == s1_id
    assert item["sub_order_id"] == sub["id"]


@pytest.mark.anyio
async def test_multi_vendor_cart_checkout_creates_partitioned_sub_orders(
    async_client: AsyncClient,
    customer_user: User,
    seller_one: User,
    seller_two: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    v2_id = str(default_catalog["v2"].id)
    s1_id = str(seller_one.id)
    s2_id = str(seller_two.id)
    headers = auth_headers_helper(customer_user)

    # Add items from 2 sellers
    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 1},
        headers=headers,
    )
    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v2_id, "quantity": 2},
        headers=headers,
    )

    response = await async_client.post("/api/v1/checkout", headers=headers)
    assert response.status_code == 201
    data = response.json()

    # Total = 95*1 + 180*2 = 455
    assert Decimal(str(data["total"])) == Decimal("455.00")
    assert len(data["sub_orders"]) == 2

    # Verify sub_orders correspond to the 2 distinct sellers
    seller_ids = {s["seller_id"] for s in data["sub_orders"]}
    assert seller_ids == {s1_id, s2_id}

    s1_sub = next(s for s in data["sub_orders"] if s["seller_id"] == s1_id)
    s2_sub = next(s for s in data["sub_orders"] if s["seller_id"] == s2_id)

    assert Decimal(str(s1_sub["total"])) == Decimal("95.00")
    assert Decimal(str(s2_sub["total"])) == Decimal("360.00")

    # Verify each order item has correct seller_id and sub_order_id
    for item in data["items"]:
        assert item["seller_id"] in (s1_id, s2_id)
        assert item["sub_order_id"] in (s1_sub["id"], s2_sub["id"])


# --- Seller Fulfillment Lifecycle Tests ---

@pytest.mark.anyio
async def test_seller_fulfillment_lifecycle(
    async_client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    headers_cust = auth_headers_helper(customer_user)
    headers_s1 = auth_headers_helper(seller_one)

    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 1},
        headers=headers_cust,
    )

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout_res.status_code == 201
    order_data = checkout_res.json()
    order_id = order_data["id"]
    sub_id = order_data["sub_orders"][0]["id"]

    # In marketplace lifecycle, once customer pays, order transitions to CONFIRMED
    sub_entity = (await db_session.execute(select(SubOrder).where(SubOrder.id == uuid.UUID(sub_id)))).scalar_one()
    sub_entity.status = OrderStatus.CONFIRMED
    await db_session.commit()

    # 1. Update to PROCESSING
    proc_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={"status": "PROCESSING"},
    )
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "PROCESSING"

    # 2. Update to SHIPPED with carrier and tracking
    ship_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={
            "status": "SHIPPED",
            "carrier": "DHL Express",
            "tracking_number": "DHL-123456789",
        },
    )
    assert ship_res.status_code == 200
    ship_data = ship_res.json()
    assert ship_data["status"] == "SHIPPED"
    assert ship_data["carrier"] == "DHL Express"
    assert ship_data["tracking_number"] == "DHL-123456789"
    assert ship_data["shipped_at"] is not None

    # 3. Update to DELIVERED
    deliv_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={"status": "DELIVERED"},
    )
    assert deliv_res.status_code == 200
    assert deliv_res.json()["status"] == "DELIVERED"
    assert deliv_res.json()["delivered_at"] is not None

    # 4. Reject invalid transition (DELIVERED -> CONFIRMED)
    invalid_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={"status": "CONFIRMED"},
    )
    assert invalid_res.status_code == 400
    assert "invalid status transition" in invalid_res.json()["detail"].lower()


@pytest.mark.anyio
async def test_seller_cannot_fulfill_other_seller_sub_order(
    async_client: AsyncClient,
    customer_user: User,
    seller_one: User,
    seller_two: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    headers_cust = auth_headers_helper(customer_user)
    headers_s2 = auth_headers_helper(seller_two)

    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 1},
        headers=headers_cust,
    )

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout_res.status_code == 201
    order_id = checkout_res.json()["id"]

    # Seller_two attempts to fulfill seller_one's order -> 404/403
    tamper_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s2,
        json={"status": "SHIPPED", "tracking_number": "FAKE-999"},
    )
    assert tamper_res.status_code in (403, 404)


@pytest.mark.anyio
async def test_customer_order_detail_includes_sub_orders_and_tracking(
    async_client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    seller_one: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    headers_cust = auth_headers_helper(customer_user)
    headers_s1 = auth_headers_helper(seller_one)

    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 1},
        headers=headers_cust,
    )

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout_res.status_code == 201
    order_id = checkout_res.json()["id"]
    sub_id = checkout_res.json()["sub_orders"][0]["id"]

    # Transition to CONFIRMED so seller can fulfill
    sub_entity = (await db_session.execute(select(SubOrder).where(SubOrder.id == uuid.UUID(sub_id)))).scalar_one()
    sub_entity.status = OrderStatus.CONFIRMED
    await db_session.commit()

    # Seller transitions to PROCESSING then SHIPPED
    proc_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={"status": "PROCESSING"},
    )
    assert proc_res.status_code == 200

    ship_res = await async_client.patch(
        f"/api/v1/seller/orders/{order_id}/fulfillment",
        headers=headers_s1,
        json={"status": "SHIPPED", "carrier": "FedEx", "tracking_number": "FDX-777888"},
    )
    assert ship_res.status_code == 200

    # Customer fetches their order details
    order_res = await async_client.get(f"/api/v1/orders/{order_id}", headers=headers_cust)
    assert order_res.status_code == 200
    order_detail = order_res.json()
    assert len(order_detail["sub_orders"]) == 1
    sub = order_detail["sub_orders"][0]
    assert sub["status"] == "SHIPPED"
    assert sub["carrier"] == "FedEx"
    assert sub["tracking_number"] == "FDX-777888"


@pytest.mark.anyio
async def test_admin_can_access_orders_and_sub_orders(
    async_client: AsyncClient,
    customer_user: User,
    admin_user: User,
    default_catalog: dict,
    auth_headers_helper,
):
    v1_id = str(default_catalog["v1"].id)
    headers_cust = auth_headers_helper(customer_user)
    headers_admin = auth_headers_helper(admin_user)

    await async_client.post(
        "/api/v1/cart/items",
        json={"variant_id": v1_id, "quantity": 1},
        headers=headers_cust,
    )

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout_res.status_code == 201
    order_id = checkout_res.json()["id"]

    # Admin accesses the order via customer route and admin route
    res_direct = await async_client.get(f"/api/v1/orders/{order_id}", headers=headers_admin)
    assert res_direct.status_code == 200
    assert len(res_direct.json()["sub_orders"]) == 1

    res_admin_list = await async_client.get("/api/v1/admin/orders", headers=headers_admin)
    assert res_admin_list.status_code == 200
    orders_list = res_admin_list.json()
    assert any(o["id"] == order_id for o in orders_list)
