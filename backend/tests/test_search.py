import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.modules.catalog.enums import ProductStatus
from app.modules.users.enums import UserRole


@pytest.fixture
async def search_test_setup(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Fixture creating brands, categories, products, variants, and stock for search tests."""
    admin = await create_user_helper(email="search_admin@example.com", role=UserRole.ADMIN)
    seller = await create_user_helper(email="search_seller@example.com", role=UserRole.SELLER)
    admin_headers = auth_headers_helper(admin)
    seller_headers = auth_headers_helper(seller)

    # 1. Create Brands
    brand1_res = await async_client.post(
        "/api/v1/brands",
        json={"name": "Prada Luxury", "description": "Italian luxury fashion house"},
        headers=admin_headers,
    )
    brand1 = brand1_res.json()

    brand2_res = await async_client.post(
        "/api/v1/brands",
        json={"name": "Nike Sportswear", "description": "Athletic and streetwear"},
        headers=admin_headers,
    )
    brand2 = brand2_res.json()

    # 2. Create Categories
    cat1_res = await async_client.post(
        "/api/v1/categories",
        json={"name": "Evening Dresses", "description": "Formal and gala wear"},
        headers=admin_headers,
    )
    cat1 = cat1_res.json()

    cat2_res = await async_client.post(
        "/api/v1/categories",
        json={"name": "Outerwear & Coats", "description": "Jackets and winter wear"},
        headers=admin_headers,
    )
    cat2 = cat2_res.json()

    # 3. Create Products
    # Product A: Velvet Gala Dress (Brand 1, Cat 1, ACTIVE, base_price=150.00)
    prod_a_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Velvet Gala Evening Dress",
            "slug": "velvet-gala-evening-dress",
            "description": "Floor-length silk and velvet gown in Emerald Green",
            "brand_id": brand1["id"],
            "category_id": cat1["id"],
            "base_price": "150.00",
            "status": "ACTIVE",
            "is_active": True,
        },
        headers=seller_headers,
    )
    prod_a = prod_a_res.json()

    # Product A Variants:
    # Var A1: Size M, Color Emerald, Price 150.00, in stock (10 units)
    var_a1_res = await async_client.post(
        f"/api/v1/products/{prod_a['id']}/variants",
        json={"sku": "VELVET-M-EMR", "color": "Emerald", "size": "M", "price": "150.00", "is_active": True},
        headers=seller_headers,
    )
    var_a1 = var_a1_res.json()
    await async_client.patch(
        f"/api/v1/inventory/{var_a1['id']}",
        json={"quantity_on_hand": 10},
        headers=seller_headers,
    )

    # Var A2: Size L, Color Emerald, Price 160.00, out of stock (0 units)
    var_a2_res = await async_client.post(
        f"/api/v1/products/{prod_a['id']}/variants",
        json={"sku": "VELVET-L-EMR", "color": "Emerald", "size": "L", "price": "160.00", "is_active": True},
        headers=seller_headers,
    )
    var_a2 = var_a2_res.json()

    # Product B: Cashmere Overcoat (Brand 1, Cat 2, ACTIVE, base_price=350.00)
    prod_b_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Italian Cashmere Overcoat",
            "slug": "italian-cashmere-overcoat",
            "description": "Double-breasted tailoring crafted with 100% fine wool",
            "brand_id": brand1["id"],
            "category_id": cat2["id"],
            "base_price": "350.00",
            "status": "ACTIVE",
            "is_active": True,
        },
        headers=seller_headers,
    )
    prod_b = prod_b_res.json()

    # Var B1: Size XL, Color Midnight Black, Price 350.00, in stock (5 units)
    var_b1_res = await async_client.post(
        f"/api/v1/products/{prod_b['id']}/variants",
        json={"sku": "COAT-XL-BLK", "color": "Midnight Black", "size": "XL", "price": "350.00", "is_active": True},
        headers=seller_headers,
    )
    var_b1 = var_b1_res.json()
    await async_client.patch(
        f"/api/v1/inventory/{var_b1['id']}",
        json={"quantity_on_hand": 5},
        headers=seller_headers,
    )

    # Product C: Windrunner Jacket (Brand 2, Cat 2, ACTIVE, base_price=90.00)
    prod_c_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Windrunner Running Jacket",
            "slug": "windrunner-running-jacket",
            "description": "Lightweight breathable windbreaker for modern runners",
            "brand_id": brand2["id"],
            "category_id": cat2["id"],
            "base_price": "90.00",
            "status": "ACTIVE",
            "is_active": True,
        },
        headers=seller_headers,
    )
    prod_c = prod_c_res.json()

    # Var C1: Size S, Color Obsidian, Price 90.00, in stock (15 units)
    var_c1_res = await async_client.post(
        f"/api/v1/products/{prod_c['id']}/variants",
        json={"sku": "RUN-S-OBS", "color": "Obsidian", "size": "S", "price": "90.00", "is_active": True},
        headers=seller_headers,
    )
    var_c1 = var_c1_res.json()
    await async_client.patch(
        f"/api/v1/inventory/{var_c1['id']}",
        json={"quantity_on_hand": 15},
        headers=seller_headers,
    )

    # Product D: DRAFT Product (should never appear in search)
    prod_d_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Secret Unreleased Velvet Dress",
            "base_price": "200.00",
            "status": "DRAFT",
            "is_active": True,
        },
        headers=seller_headers,
    )
    prod_d = prod_d_res.json()

    # Product E: ARCHIVED Product (should never appear in search)
    prod_e_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Archived Vintage Velvet Robe",
            "base_price": "80.00",
            "status": "ACTIVE",
            "is_active": True,
        },
        headers=seller_headers,
    )
    prod_e = prod_e_res.json()
    await async_client.patch(
        f"/api/v1/products/{prod_e['id']}",
        json={"status": "ARCHIVED"},
        headers=seller_headers,
    )

    # Product F: INACTIVE Product (is_active=False, should never appear in search)
    prod_f_res = await async_client.post(
        "/api/v1/products",
        json={
            "name": "Deactivated Velvet Cape",
            "base_price": "110.00",
            "status": "ACTIVE",
            "is_active": False,
        },
        headers=seller_headers,
    )
    prod_f = prod_f_res.json()

    return {
        "admin": admin,
        "seller": seller,
        "brand1": brand1,
        "brand2": brand2,
        "cat1": cat1,
        "cat2": cat2,
        "prod_a": prod_a,
        "prod_b": prod_b,
        "prod_c": prod_c,
        "prod_d": prod_d,
        "prod_e": prod_e,
        "prod_f": prod_f,
        "var_a1": var_a1,
        "var_a2": var_a2,
        "var_b1": var_b1,
        "var_c1": var_c1,
    }


# ==============================================================================
# Search Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_01_empty_query_lists_active_products(async_client: AsyncClient, search_test_setup):
    """GET /api/v1/search/products with empty q returns all active marketplace products."""
    res = await async_client.get("/api/v1/search/products")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 20

    ids = [item["id"] for item in data["items"]]
    assert search_test_setup["prod_a"]["id"] in ids
    assert search_test_setup["prod_b"]["id"] in ids
    assert search_test_setup["prod_c"]["id"] in ids


@pytest.mark.asyncio
async def test_02_search_by_product_name_case_insensitive(async_client: AsyncClient, search_test_setup):
    """Search matches product name case-insensitively."""
    # lowercase
    res1 = await async_client.get("/api/v1/search/products?q=velvet")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["id"] == search_test_setup["prod_a"]["id"]

    # uppercase
    res2 = await async_client.get("/api/v1/search/products?q=VELVET")
    assert res2.status_code == 200
    assert res2.json()["total"] == 1
    assert res2.json()["items"][0]["id"] == search_test_setup["prod_a"]["id"]


@pytest.mark.asyncio
async def test_03_search_by_description(async_client: AsyncClient, search_test_setup):
    """Search matches terms in product description."""
    res = await async_client.get("/api/v1/search/products?q=tailoring")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == search_test_setup["prod_b"]["id"]


@pytest.mark.asyncio
async def test_04_search_by_slug(async_client: AsyncClient, search_test_setup):
    """Search matches product slug."""
    res = await async_client.get("/api/v1/search/products?q=windrunner-running")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == search_test_setup["prod_c"]["id"]


@pytest.mark.asyncio
async def test_05_search_by_variant_sku_color_size(async_client: AsyncClient, search_test_setup):
    """Search matches variant SKU, color, or size."""
    # By SKU
    res_sku = await async_client.get("/api/v1/search/products?q=COAT-XL-BLK")
    assert res_sku.status_code == 200
    assert res_sku.json()["total"] == 1
    assert res_sku.json()["items"][0]["id"] == search_test_setup["prod_b"]["id"]

    # By Color
    res_col = await async_client.get("/api/v1/search/products?q=Obsidian")
    assert res_col.status_code == 200
    assert res_col.json()["total"] == 1
    assert res_col.json()["items"][0]["id"] == search_test_setup["prod_c"]["id"]


@pytest.mark.asyncio
async def test_06_search_by_brand_and_category_name(async_client: AsyncClient, search_test_setup):
    """Search matches brand name and category name."""
    # Brand
    res_b = await async_client.get("/api/v1/search/products?q=Nike")
    assert res_b.status_code == 200
    assert any(item["id"] == search_test_setup["prod_c"]["id"] for item in res_b.json()["items"])

    # Category
    res_c = await async_client.get("/api/v1/search/products?q=Outerwear")
    assert res_c.status_code == 200
    coat_ids = [item["id"] for item in res_c.json()["items"]]
    assert search_test_setup["prod_b"]["id"] in coat_ids
    assert search_test_setup["prod_c"]["id"] in coat_ids


@pytest.mark.asyncio
async def test_07_deterministic_relevance_ranking(async_client: AsyncClient, search_test_setup, create_user_helper, auth_headers_helper):
    """Relevance priority ranks exact product name match before partial and description matches."""
    seller_headers = auth_headers_helper(search_test_setup["seller"])

    # Product with exact name "Silk Dress"
    p_exact = await async_client.post(
        "/api/v1/products",
        json={"name": "Silk Dress", "base_price": "200.00", "status": "ACTIVE", "is_active": True},
        headers=seller_headers,
    )
    # Product with starting name "Silk Dress for Summer"
    p_starts = await async_client.post(
        "/api/v1/products",
        json={"name": "Silk Dress for Summer", "base_price": "180.00", "status": "ACTIVE", "is_active": True},
        headers=seller_headers,
    )
    # Product with containing name "Classic Vintage Silk Dress Long"
    p_contains = await async_client.post(
        "/api/v1/products",
        json={"name": "Classic Vintage Silk Dress Long", "base_price": "220.00", "status": "ACTIVE", "is_active": True},
        headers=seller_headers,
    )

    res = await async_client.get("/api/v1/search/products?q=Silk Dress&sort=relevance")
    assert res.status_code == 200
    items = res.json()["items"]
    ids = [i["id"] for i in items]

    assert ids.index(p_exact.json()["id"]) < ids.index(p_starts.json()["id"])
    assert ids.index(p_starts.json()["id"]) < ids.index(p_contains.json()["id"])


# ==============================================================================
# Filtering Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_08_filter_by_category_id(async_client: AsyncClient, search_test_setup):
    """Filter by category_id returns only products assigned to that category."""
    cat_id = search_test_setup["cat1"]["id"]
    res = await async_client.get(f"/api/v1/search/products?category_id={cat_id}")
    assert res.status_code == 200
    data = res.json()
    assert all(item["category"]["id"] == cat_id for item in data["items"])
    assert any(item["id"] == search_test_setup["prod_a"]["id"] for item in data["items"])


@pytest.mark.asyncio
async def test_09_filter_by_brand_id(async_client: AsyncClient, search_test_setup):
    """Filter by brand_id returns only products from that brand."""
    brand_id = search_test_setup["brand2"]["id"]
    res = await async_client.get(f"/api/v1/search/products?brand_id={brand_id}")
    assert res.status_code == 200
    data = res.json()
    assert all(item["brand"]["id"] == brand_id for item in data["items"])
    assert any(item["id"] == search_test_setup["prod_c"]["id"] for item in data["items"])


@pytest.mark.asyncio
async def test_10_filter_by_price_range(async_client: AsyncClient, search_test_setup):
    """Filter by min_price and max_price restricts results to products in that range."""
    # Min price 100.00, Max price 200.00
    res = await async_client.get("/api/v1/search/products?min_price=100.00&max_price=200.00")
    assert res.status_code == 200
    data = res.json()
    ids = [item["id"] for item in data["items"]]
    assert search_test_setup["prod_a"]["id"] in ids
    assert search_test_setup["prod_b"]["id"] not in ids
    assert search_test_setup["prod_c"]["id"] not in ids


@pytest.mark.asyncio
async def test_11_filter_by_size_and_color(async_client: AsyncClient, search_test_setup):
    """Filter by variant size and color matches products with corresponding active variants."""
    res_size = await async_client.get("/api/v1/search/products?size=XL")
    assert res_size.status_code == 200
    ids_size = [item["id"] for item in res_size.json()["items"]]
    assert search_test_setup["prod_b"]["id"] in ids_size

    res_color = await async_client.get("/api/v1/search/products?color=Emerald")
    assert res_color.status_code == 200
    ids_color = [item["id"] for item in res_color.json()["items"]]
    assert search_test_setup["prod_a"]["id"] in ids_color


@pytest.mark.asyncio
async def test_12_filter_by_in_stock(async_client: AsyncClient, search_test_setup, create_user_helper, auth_headers_helper):
    """Filter in_stock=true returns only products with at least one active variant with available stock."""
    seller_headers = auth_headers_helper(search_test_setup["seller"])

    # Create a product with 0 stock on all variants
    p_zero = await async_client.post(
        "/api/v1/products",
        json={"name": "Zero Stock T-Shirt", "base_price": "25.00", "status": "ACTIVE", "is_active": True},
        headers=seller_headers,
    )
    p_zero_id = p_zero.json()["id"]
    await async_client.post(
        f"/api/v1/products/{p_zero_id}/variants",
        json={"sku": "ZERO-S", "size": "S", "price": "25.00", "is_active": True},
        headers=seller_headers,
    )
    # Default inventory created is 0 on hand

    res = await async_client.get("/api/v1/search/products?in_stock=true")
    assert res.status_code == 200
    ids = [i["id"] for i in res.json()["items"]]
    assert p_zero_id not in ids
    assert search_test_setup["prod_a"]["id"] in ids
    assert search_test_setup["prod_b"]["id"] in ids
    assert search_test_setup["prod_c"]["id"] in ids


@pytest.mark.asyncio
async def test_13_no_duplicate_products_when_multiple_variants_match(
    async_client: AsyncClient, search_test_setup, create_user_helper, auth_headers_helper
):
    """When a product has multiple variants matching search/filters, it appears only once."""
    seller_headers = auth_headers_helper(search_test_setup["seller"])

    p_multi = await async_client.post(
        "/api/v1/products",
        json={"name": "Multi Variant Denim", "base_price": "75.00", "status": "ACTIVE", "is_active": True},
        headers=seller_headers,
    )
    pid = p_multi.json()["id"]

    # 3 active variants with same color 'Blue'
    for size in ["28", "30", "32"]:
        await async_client.post(
            f"/api/v1/products/{pid}/variants",
            json={"sku": f"DENIM-BLU-{size}", "color": "Blue", "size": size, "price": "75.00", "is_active": True},
            headers=seller_headers,
        )

    res = await async_client.get("/api/v1/search/products?color=Blue")
    assert res.status_code == 200
    items = res.json()["items"]
    matches = [i for i in items if i["id"] == pid]
    assert len(matches) == 1


# ==============================================================================
# Sorting & Pagination Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_14_sorting_options(async_client: AsyncClient, search_test_setup):
    """Verify supported sort orders: price_asc, price_desc, newest, oldest, name_asc, name_desc."""
    # price_asc
    res_asc = await async_client.get("/api/v1/search/products?sort=price_asc")
    assert res_asc.status_code == 200
    prices = [Decimal(i["base_price"]) for i in res_asc.json()["items"]]
    assert prices == sorted(prices)

    # price_desc
    res_desc = await async_client.get("/api/v1/search/products?sort=price_desc")
    assert res_desc.status_code == 200
    prices_desc = [Decimal(i["base_price"]) for i in res_desc.json()["items"]]
    assert prices_desc == sorted(prices_desc, reverse=True)

    # name_asc
    res_name = await async_client.get("/api/v1/search/products?sort=name_asc")
    assert res_name.status_code == 200
    names = [i["name"].lower() for i in res_name.json()["items"]]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_15_invalid_sort_and_price_range_rejected(async_client: AsyncClient):
    """Invalid sort values return 422, and min_price > max_price returns 400."""
    res_sort = await async_client.get("/api/v1/search/products?sort=arbitrary_injection")
    assert res_sort.status_code == 422

    res_price = await async_client.get("/api/v1/search/products?min_price=200&max_price=100")
    assert res_price.status_code == 400
    assert "min_price cannot be greater" in res_price.json()["detail"].lower()


@pytest.mark.asyncio
async def test_16_pagination_envelope_and_slicing(async_client: AsyncClient, search_test_setup):
    """Pagination envelope returns items, total, total_pages, has_next, has_previous."""
    res_p1 = await async_client.get("/api/v1/search/products?page=1&page_size=2")
    assert res_p1.status_code == 200
    d1 = res_p1.json()
    assert d1["page"] == 1
    assert d1["page_size"] == 2
    assert len(d1["items"]) == 2
    assert d1["has_next"] is True
    assert d1["has_previous"] is False

    res_p2 = await async_client.get("/api/v1/search/products?page=2&page_size=2")
    assert res_p2.status_code == 200
    d2 = res_p2.json()
    assert d2["page"] == 2
    assert d2["has_previous"] is True

    # Check distinct items between page 1 and page 2
    p1_ids = {i["id"] for i in d1["items"]}
    p2_ids = {i["id"] for i in d2["items"]}
    assert p1_ids.isdisjoint(p2_ids)


# ==============================================================================
# Security & Privacy Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_17_security_draft_archived_inactive_products_never_leaked(async_client: AsyncClient, search_test_setup):
    """Draft, archived, and is_active=False products are strictly excluded from search."""
    draft_id = search_test_setup["prod_d"]["id"]
    archived_id = search_test_setup["prod_e"]["id"]
    inactive_id = search_test_setup["prod_f"]["id"]

    res = await async_client.get("/api/v1/search/products")
    assert res.status_code == 200
    returned_ids = [item["id"] for item in res.json()["items"]]

    assert draft_id not in returned_ids
    assert archived_id not in returned_ids
    assert inactive_id not in returned_ids


@pytest.mark.asyncio
async def test_18_security_inactive_variants_never_leaked(
    async_client: AsyncClient, search_test_setup, create_user_helper, auth_headers_helper
):
    """Inactive variants are omitted from public search item variant lists."""
    seller_headers = auth_headers_helper(search_test_setup["seller"])
    prod_id = search_test_setup["prod_a"]["id"]

    # Add an inactive variant
    inact_var = await async_client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"sku": "INACT-SKU-99", "size": "XXL", "price": "199.00", "is_active": False},
        headers=seller_headers,
    )
    inact_var_id = inact_var.json()["id"]

    res = await async_client.get(f"/api/v1/search/products?q=Velvet")
    assert res.status_code == 200
    prod_item = next(i for i in res.json()["items"] if i["id"] == prod_id)
    variant_ids = [v["id"] for v in prod_item["variants"]]
    assert inact_var_id not in variant_ids


@pytest.mark.asyncio
async def test_19_security_stock_privacy_preserved(async_client: AsyncClient, search_test_setup):
    """Search endpoints expose only is_in_stock boolean, never raw quantity_on_hand or reserved."""
    res = await async_client.get("/api/v1/search/products")
    assert res.status_code == 200
    items = res.json()["items"]

    for item in items:
        assert "quantity_on_hand" not in item
        assert "quantity_reserved" not in item
        assert isinstance(item["is_in_stock"], bool)
        for var in item["variants"]:
            assert "quantity_on_hand" not in var
            assert "quantity_reserved" not in var
            assert isinstance(var["is_in_stock"], bool)


# ==============================================================================
# Filter Metadata Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_20_filter_options_endpoint(async_client: AsyncClient, search_test_setup):
    """GET /api/v1/search/filters returns active categories, brands, sizes, colors, and price bounds."""
    res = await async_client.get("/api/v1/search/filters")
    assert res.status_code == 200
    data = res.json()

    assert "categories" in data
    assert "brands" in data
    assert "sizes" in data
    assert "colors" in data
    assert "min_price" in data
    assert "max_price" in data

    # Check categories
    cat_ids = [c["id"] for c in data["categories"]]
    assert search_test_setup["cat1"]["id"] in cat_ids
    assert search_test_setup["cat2"]["id"] in cat_ids

    # Check brands
    brand_ids = [b["id"] for b in data["brands"]]
    assert search_test_setup["brand1"]["id"] in brand_ids
    assert search_test_setup["brand2"]["id"] in brand_ids

    # Check sizes and colors
    assert "M" in data["sizes"]
    assert "XL" in data["sizes"]
    assert "Emerald" in data["colors"]

    # Check price bounds
    min_p = Decimal(str(data["min_price"]))
    max_p = Decimal(str(data["max_price"]))
    assert min_p > 0
    assert max_p >= min_p
