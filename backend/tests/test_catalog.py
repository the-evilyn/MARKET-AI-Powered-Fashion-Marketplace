import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.modules.catalog.enums import MediaType, ProductStatus
from app.modules.catalog.models import Brand, Category, Product
from app.modules.users.enums import UserRole


# ==============================================================================
# Brand Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_can_create_brand(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Admin can create a new brand."""
    admin = await create_user_helper(email="admin_brand@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    payload = {
        "name": "Acne Studios",
        "description": "Stockholm-based multidisciplinary luxury fashion house",
        "logo_url": "https://cdn.example.com/brands/acne.png",
    }
    response = await async_client.post("/api/v1/brands", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acne Studios"
    assert data["slug"] == "acne-studios"
    assert data["logo_url"] == "https://cdn.example.com/brands/acne.png"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_customer_cannot_create_brand(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Customer role is forbidden from creating brands."""
    customer = await create_user_helper(email="cust_brand@example.com", role=UserRole.CUSTOMER)
    headers = auth_headers_helper(customer)

    payload = {"name": "Unauthorized Label"}
    response = await async_client.post("/api/v1/brands", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_create_brand(async_client: AsyncClient):
    """Unauthenticated request cannot create brands."""
    response = await async_client.post("/api/v1/brands", json={"name": "No Auth Brand"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_brand_slug_rejected(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Attempting to create a duplicate brand slug returns 400 Bad Request."""
    admin = await create_user_helper(email="admin_dup_brand@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    res1 = await async_client.post("/api/v1/brands", json={"name": "Prada", "slug": "prada"}, headers=headers)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/brands", json={"name": "Prada Milano", "slug": "prada"}, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_brand_by_id_and_list(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Public retrieval of brands by ID and list."""
    admin = await create_user_helper(email="admin_list_brand@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    res = await async_client.post("/api/v1/brands", json={"name": "Gucci"}, headers=headers)
    brand_id = res.json()["id"]

    # Public list
    list_res = await async_client.get("/api/v1/brands")
    assert list_res.status_code == 200
    assert any(b["id"] == brand_id for b in list_res.json())

    # Public get by ID
    get_res = await async_client.get(f"/api/v1/brands/{brand_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Gucci"


@pytest.mark.asyncio
async def test_admin_can_update_and_delete_brand(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Admin can update and delete brands."""
    admin = await create_user_helper(email="admin_del_brand@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    create_res = await async_client.post("/api/v1/brands", json={"name": "Old Brand"}, headers=headers)
    brand_id = create_res.json()["id"]

    # Update
    patch_res = await async_client.patch(
        f"/api/v1/brands/{brand_id}",
        json={"name": "Updated Brand", "description": "New description"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Brand"
    assert patch_res.json()["description"] == "New description"

    # Delete
    del_res = await async_client.delete(f"/api/v1/brands/{brand_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm 404
    get_res = await async_client.get(f"/api/v1/brands/{brand_id}")
    assert get_res.status_code == 404


# ==============================================================================
# Category Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_can_create_root_and_child_category(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Admin can create a root category and nested child category hierarchy."""
    admin = await create_user_helper(email="admin_cat@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    # Root Category: Women
    root_res = await async_client.post("/api/v1/categories", json={"name": "Women"}, headers=headers)
    assert root_res.status_code == 201
    root_data = root_res.json()
    assert root_data["name"] == "Women"
    assert root_data["slug"] == "women"
    assert root_data["parent_id"] is None

    # Child Category: Dresses
    child_res = await async_client.post(
        "/api/v1/categories",
        json={"name": "Dresses", "parent_id": root_data["id"]},
        headers=headers,
    )
    assert child_res.status_code == 201
    child_data = child_res.json()
    assert child_data["name"] == "Dresses"
    assert child_data["slug"] == "dresses"
    assert child_data["parent_id"] == root_data["id"]

    # Grandchild Category: Evening Dresses
    grandchild_res = await async_client.post(
        "/api/v1/categories",
        json={"name": "Evening Dresses", "parent_id": child_data["id"]},
        headers=headers,
    )
    assert grandchild_res.status_code == 201
    assert grandchild_res.json()["parent_id"] == child_data["id"]


@pytest.mark.asyncio
async def test_reject_category_self_parent(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Updating a category to be its own parent is rejected."""
    admin = await create_user_helper(email="admin_self_cat@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    cat_res = await async_client.post("/api/v1/categories", json={"name": "Outerwear"}, headers=headers)
    cat_id = cat_res.json()["id"]

    patch_res = await async_client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"parent_id": cat_id},
        headers=headers,
    )
    assert patch_res.status_code == 400
    assert "cannot be its own parent" in patch_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_category_slug_rejected(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Duplicate category slugs are rejected with 400."""
    admin = await create_user_helper(email="admin_dup_cat@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    res1 = await async_client.post("/api/v1/categories", json={"name": "Shoes", "slug": "shoes"}, headers=headers)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/categories", json={"name": "Footwear", "slug": "shoes"}, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_and_delete_category(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Admin can update category metadata and delete it."""
    admin = await create_user_helper(email="admin_ud_cat@example.com", role=UserRole.ADMIN)
    headers = auth_headers_helper(admin)

    cat_res = await async_client.post("/api/v1/categories", json={"name": "Accessories"}, headers=headers)
    cat_id = cat_res.json()["id"]

    update_res = await async_client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Luxury Accessories", "description": "Bags, belts, scarves"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Luxury Accessories"
    assert update_res.json()["description"] == "Bags, belts, scarves"

    del_res = await async_client.delete(f"/api/v1/categories/{cat_id}", headers=headers)
    assert del_res.status_code == 204


# ==============================================================================
# Product Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_seller_can_create_product(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Seller can create a product listing; ownership is bound to seller."""
    seller = await create_user_helper(email="seller1@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    payload = {
        "name": "Silk Slip Dress",
        "description": "100% Mulberry silk bias cut evening slip dress",
        "status": "DRAFT",
        "base_price": "280.00",
        "currency": "USD",
    }
    response = await async_client.post("/api/v1/products", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Silk Slip Dress"
    assert data["slug"] == "silk-slip-dress"
    assert data["seller_id"] == str(seller.id)
    assert data["base_price"] == "280.00"
    assert data["currency"] == "USD"
    assert data["status"] == "DRAFT"
    assert data["brand_id"] is None
    assert data["category_id"] is None


@pytest.mark.asyncio
async def test_customer_cannot_create_product(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Customer role cannot create products."""
    customer = await create_user_helper(email="buyer@example.com", role=UserRole.CUSTOMER)
    headers = auth_headers_helper(customer)

    payload = {
        "name": "Customer Product Attempt",
        "base_price": "50.00",
    }
    response = await async_client.post("/api/v1/products", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_seller_cannot_modify_another_seller_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Seller cannot update or delete products owned by a different seller."""
    seller1 = await create_user_helper(email="seller_a@example.com", role=UserRole.SELLER)
    seller2 = await create_user_helper(email="seller_b@example.com", role=UserRole.SELLER)

    headers1 = auth_headers_helper(seller1)
    headers2 = auth_headers_helper(seller2)

    # Seller 1 creates a product
    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Seller 1 Jacket", "base_price": "199.00"},
        headers=headers1,
    )
    product_id = prod_res.json()["id"]

    # Seller 2 tries to update Seller 1's product -> 403 Forbidden
    patch_res = await async_client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Hacked Jacket"},
        headers=headers2,
    )
    assert patch_res.status_code == 403

    # Seller 2 tries to delete Seller 1's product -> 403 Forbidden
    del_res = await async_client.delete(f"/api/v1/products/{product_id}", headers=headers2)
    assert del_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_manage_products(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Admin can update and delete any product regardless of seller ownership."""
    seller = await create_user_helper(email="seller_c@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="admin_prod@example.com", role=UserRole.ADMIN)

    seller_headers = auth_headers_helper(seller)
    admin_headers = auth_headers_helper(admin)

    # Seller creates product
    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Seller Boots", "base_price": "350.00"},
        headers=seller_headers,
    )
    product_id = prod_res.json()["id"]

    # Admin updates product
    patch_res = await async_client.patch(
        f"/api/v1/products/{product_id}",
        json={"status": "ACTIVE"},
        headers=admin_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACTIVE"

    # Admin deletes product
    del_res = await async_client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_invalid_negative_price_rejected(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Negative base prices are rejected by validation schema."""
    seller = await create_user_helper(email="seller_neg@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    response = await async_client.post(
        "/api/v1/products",
        json={"name": "Free negative dress", "base_price": "-10.00"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_product_slug_rejected(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Creating a product with an existing slug returns 400 Bad Request."""
    seller = await create_user_helper(email="seller_dup@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    res1 = await async_client.post(
        "/api/v1/products",
        json={"name": "Cashmere Knit Sweater", "slug": "cashmere-knit", "base_price": "220.00"},
        headers=headers,
    )
    assert res1.status_code == 201

    res2 = await async_client.post(
        "/api/v1/products",
        json={"name": "Cashmere Knit Cardigan", "slug": "cashmere-knit", "base_price": "240.00"},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_can_list_and_get_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Public/unauthenticated users can query the product catalog."""
    seller = await create_user_helper(email="seller_pub@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    create_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Trench Coat", "base_price": "450.00"},
        headers=headers,
    )
    product_id = create_res.json()["id"]

    # Public list
    list_res = await async_client.get("/api/v1/products")
    assert list_res.status_code == 200
    assert any(p["id"] == product_id for p in list_res.json())

    # Public get
    get_res = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Trench Coat"


# ==============================================================================
# Product Variant Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_seller_can_create_variant_for_own_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Seller can create SKU variants for their own products."""
    seller = await create_user_helper(email="seller_var@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Classic Oversized Tee", "base_price": "45.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    variant_payload = {
        "sku": "TEE-BLK-M",
        "color": "Black",
        "size": "M",
        "price": "45.00",
        "compare_at_price": "60.00",
    }
    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json=variant_payload,
        headers=headers,
    )
    assert var_res.status_code == 201
    data = var_res.json()
    assert data["sku"] == "TEE-BLK-M"
    assert data["color"] == "Black"
    assert data["size"] == "M"
    assert data["price"] == "45.00"
    assert data["compare_at_price"] == "60.00"
    assert data["product_id"] == product_id


@pytest.mark.asyncio
async def test_seller_cannot_create_variant_for_another_seller_product(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Seller cannot add variants to another seller's product."""
    seller1 = await create_user_helper(email="s1_var@example.com", role=UserRole.SELLER)
    seller2 = await create_user_helper(email="s2_var@example.com", role=UserRole.SELLER)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Silk Scarf", "base_price": "80.00"},
        headers=auth_headers_helper(seller1),
    )
    product_id = prod_res.json()["id"]

    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "SCARF-RED", "price": "80.00"},
        headers=auth_headers_helper(seller2),
    )
    assert var_res.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_sku_rejected(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Duplicate variant SKUs are rejected with 400 Bad Request."""
    seller = await create_user_helper(email="seller_sku@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Wool Beanie", "base_price": "35.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    res1 = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "BEANIE-GRY-OS", "price": "35.00"},
        headers=headers,
    )
    assert res1.status_code == 201

    res2 = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "BEANIE-GRY-OS", "price": "35.00"},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_variant_price_validations(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Negative prices and invalid compare_at_prices are rejected."""
    seller = await create_user_helper(email="seller_vp@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Linen Pants", "base_price": "120.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    # Negative price rejected
    neg_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "LP-NEG", "price": "-20.00"},
        headers=headers,
    )
    assert neg_res.status_code == 422

    # compare_at_price less than price rejected
    comp_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "LP-COMP", "price": "120.00", "compare_at_price": "90.00"},
        headers=headers,
    )
    assert comp_res.status_code == 422


@pytest.mark.asyncio
async def test_update_and_delete_variant(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Owner seller can update and delete variants."""
    seller = await create_user_helper(email="seller_ud_var@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Pleated Skirt", "base_price": "95.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "SKIRT-BLK-S", "price": "95.00"},
        headers=headers,
    )
    variant_id = var_res.json()["id"]

    # Update variant
    patch_res = await async_client.patch(
        f"/api/v1/products/{product_id}/variants/{variant_id}",
        json={"price": "85.00", "compare_at_price": "100.00", "color": "Jet Black"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["price"] == "85.00"
    assert patch_res.json()["color"] == "Jet Black"

    # Delete variant
    del_res = await async_client.delete(
        f"/api/v1/products/{product_id}/variants/{variant_id}",
        headers=headers,
    )
    assert del_res.status_code == 204


# ==============================================================================
# Product Media Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_seller_can_manage_own_product_media(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Seller can add, update, and delete media for their product."""
    seller = await create_user_helper(email="seller_media@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Leather Biker Jacket", "base_price": "600.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    # Add media
    media_payload = {
        "media_type": "IMAGE",
        "url": "https://storage.example.com/products/jacket_front.webp",
        "object_key": "products/jacket_front.webp",
        "alt_text": "Front view of black leather biker jacket",
        "sort_order": 0,
        "is_primary": True,
    }
    media_res = await async_client.post(
        f"/api/v1/products/{product_id}/media",
        json=media_payload,
        headers=headers,
    )
    assert media_res.status_code == 201
    media_id = media_res.json()["id"]
    assert media_res.json()["is_primary"] is True
    assert media_res.json()["object_key"] == "products/jacket_front.webp"

    # List media
    list_res = await async_client.get(f"/api/v1/products/{product_id}/media")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Update media
    patch_res = await async_client.patch(
        f"/api/v1/products/{product_id}/media/{media_id}",
        json={"alt_text": "Updated front angle view"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["alt_text"] == "Updated front angle view"

    # Delete media
    del_res = await async_client.delete(
        f"/api/v1/products/{product_id}/media/{media_id}",
        headers=headers,
    )
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_seller_cannot_manage_another_seller_media(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """Seller cannot modify media on another seller's product."""
    seller1 = await create_user_helper(email="s1_m@example.com", role=UserRole.SELLER)
    seller2 = await create_user_helper(email="s2_m@example.com", role=UserRole.SELLER)

    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Cocktail Dress", "base_price": "210.00"},
        headers=auth_headers_helper(seller1),
    )
    product_id = prod_res.json()["id"]

    media_res = await async_client.post(
        f"/api/v1/products/{product_id}/media",
        json={"url": "https://storage.example.com/dress.jpg"},
        headers=auth_headers_helper(seller2),
    )
    assert media_res.status_code == 403


@pytest.mark.asyncio
async def test_cascade_delete_product_removes_variants_and_media(
    async_client: AsyncClient, create_user_helper, auth_headers_helper, db_session
):
    """Deleting a product cascades to delete its variants and media."""
    seller = await create_user_helper(email="seller_casc@example.com", role=UserRole.SELLER)
    headers = auth_headers_helper(seller)

    # 1. Create product
    prod_res = await async_client.post(
        "/api/v1/products",
        json={"name": "Full Suite Outfit", "base_price": "300.00"},
        headers=headers,
    )
    product_id = prod_res.json()["id"]

    # 2. Create variant
    var_res = await async_client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku": "SUITE-NAVY-40R", "price": "300.00"},
        headers=headers,
    )
    assert var_res.status_code == 201

    # 3. Create media
    media_res = await async_client.post(
        f"/api/v1/products/{product_id}/media",
        json={"url": "https://storage.example.com/suite.jpg"},
        headers=headers,
    )
    assert media_res.status_code == 201

    # 4. Delete product
    del_res = await async_client.delete(f"/api/v1/products/{product_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify product, variants, and media are gone
    get_prod = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_prod.status_code == 404

    get_var = await async_client.get(f"/api/v1/products/{product_id}/variants")
    assert get_var.status_code == 404

    get_media = await async_client.get(f"/api/v1/products/{product_id}/media")
    assert get_media.status_code == 404
