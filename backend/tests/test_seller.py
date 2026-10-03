import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.modules.catalog.enums import ProductStatus
from app.modules.orders.enums import OrderStatus
from app.modules.payments.routes import payment_service
from app.modules.users.enums import UserRole


@pytest.mark.asyncio
async def test_seller_dashboard_requires_seller_or_admin(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Customer is forbidden (403) and unauthenticated is unauthorized (401)."""
    # 1. Unauthenticated request
    res_unauth = await async_client.get("/api/v1/seller/dashboard")
    assert res_unauth.status_code == 401

    # 2. Customer request (Forbidden)
    customer = await create_user_helper(email="cust_dash@example.com", role=UserRole.CUSTOMER)
    res_cust = await async_client.get("/api/v1/seller/dashboard", headers=auth_headers_helper(customer))
    assert res_cust.status_code == 403

    # 3. Seller request (Success)
    seller = await create_user_helper(email="seller_dash@example.com", role=UserRole.SELLER)
    res_seller = await async_client.get("/api/v1/seller/dashboard", headers=auth_headers_helper(seller))
    assert res_seller.status_code == 200
    data = res_seller.json()
    assert data["total_products"] == 0
    assert data["total_sales"] == "0.00" or data["total_sales"] == 0.00 or Decimal(str(data["total_sales"])) == Decimal("0.00")


@pytest.mark.asyncio
async def test_seller_dashboard_kpis_and_isolation(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Verify seller dashboard KPIs are derived accurately and isolated between sellers."""
    seller_a = await create_user_helper(email="seller_kpi_a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="seller_kpi_b@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="admin_kpi@example.com", role=UserRole.ADMIN)
    customer = await create_user_helper(email="cust_kpi@example.com", role=UserRole.CUSTOMER)

    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)
    headers_admin = auth_headers_helper(admin)
    headers_cust = auth_headers_helper(customer)

    # 1. Seller A creates 2 products, 1 active, 1 draft
    p_a1 = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Silk Dress", "base_price": "150.00", "status": "ACTIVE"},
        headers=headers_a,
    )
    assert p_a1.status_code == 201
    pa1_id = p_a1.json()["id"]

    p_a2 = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Linen Shirt", "base_price": "80.00", "status": "DRAFT"},
        headers=headers_a,
    )
    assert p_a2.status_code == 201
    pa2_id = p_a2.json()["id"]

    # Add variants for Seller A
    v_a1 = await async_client.post(
        f"/api/v1/seller/products/{pa1_id}/variants",
        json={"sku": "SD-RED-S", "price": "150.00"},
        headers=headers_a,
    )
    assert v_a1.status_code == 201
    va1_id = v_a1.json()["id"]

    v_a2 = await async_client.post(
        f"/api/v1/seller/products/{pa1_id}/variants",
        json={"sku": "SD-RED-M", "price": "150.00"},
        headers=headers_a,
    )
    assert v_a2.status_code == 201
    va2_id = v_a2.json()["id"]

    # Stock variant 1 with 20, variant 2 with 2 (low stock <= 5)
    await async_client.patch(
        f"/api/v1/seller/inventory/{va1_id}",
        json={"quantity_on_hand": 20},
        headers=headers_a,
    )
    await async_client.patch(
        f"/api/v1/seller/inventory/{va2_id}",
        json={"quantity_on_hand": 2},
        headers=headers_a,
    )

    # 2. Seller B creates 1 product with 1 variant, stock 50
    p_b1 = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Leather Boots", "base_price": "200.00", "status": "ACTIVE"},
        headers=headers_b,
    )
    pb1_id = p_b1.json()["id"]

    v_b1 = await async_client.post(
        f"/api/v1/seller/products/{pb1_id}/variants",
        json={"sku": "BOOT-BLK-42", "price": "200.00"},
        headers=headers_b,
    )
    vb1_id = v_b1.json()["id"]

    await async_client.patch(
        f"/api/v1/seller/inventory/{vb1_id}",
        json={"quantity_on_hand": 50},
        headers=headers_b,
    )

    # 3. Customer checks out cart containing both Seller A and Seller B items
    await async_client.post("/api/v1/cart/items", json={"variant_id": va1_id, "quantity": 2}, headers=headers_cust)
    await async_client.post("/api/v1/cart/items", json={"variant_id": vb1_id, "quantity": 1}, headers=headers_cust)

    checkout_res = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout_res.status_code == 201
    order_data = checkout_res.json()
    order_id = order_data["id"]

    # At this point, order is PENDING_PAYMENT
    dash_a = (await async_client.get("/api/v1/seller/dashboard", headers=headers_a)).json()
    assert dash_a["total_products"] == 2
    assert dash_a["active_products"] == 1
    assert dash_a["total_variants"] == 2
    assert dash_a["low_stock_variants"] == 1  # va2 has 2 units (<=5)
    assert dash_a["pending_orders"] == 1
    assert dash_a["confirmed_orders"] == 0
    # Pending orders must NOT count towards sales!
    assert Decimal(str(dash_a["total_sales"])) == Decimal("0.00")
    assert dash_a["total_items_sold"] == 0

    # 4. Confirm order payment via PayPal capture (simulate confirmed payment)
    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-DASH-001", "status": "CREATED"}),
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
                                    "id": "CAPTURE-DASH-001",
                                    "status": "COMPLETED",
                                    "amount": {"currency_code": "USD", "value": "500.00"},
                                }
                            ]
                        }
                    }
                ],
            }
        ),
    ):
        create_pay = await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order_id},
            headers=headers_cust,
        )
        assert create_pay.status_code == 201
        paypal_order_id = create_pay.json()["paypal_order_id"]
        cap_res = await async_client.post(
            "/api/v1/payments/paypal/capture",
            json={"paypal_order_id": paypal_order_id},
            headers=headers_cust,
        )
        assert cap_res.status_code == 200

    # 5. Check Seller A dashboard now:
    # 2 units of va1_id sold at $150.00 = $300.00 sales, 2 items sold
    dash_a_after = (await async_client.get("/api/v1/seller/dashboard", headers=headers_a)).json()
    assert dash_a_after["total_orders"] == 1
    assert dash_a_after["pending_orders"] == 0
    assert dash_a_after["confirmed_orders"] == 1
    assert Decimal(str(dash_a_after["total_sales"])) == Decimal("300.00")
    assert dash_a_after["total_items_sold"] == 2

    # 6. Check Seller B dashboard:
    # 1 unit of vb1_id sold at $200.00 = $200.00 sales, 1 item sold
    dash_b = (await async_client.get("/api/v1/seller/dashboard", headers=headers_b)).json()
    assert dash_b["total_products"] == 1
    assert dash_b["active_products"] == 1
    assert dash_b["total_variants"] == 1
    assert dash_b["total_orders"] == 1
    assert dash_b["confirmed_orders"] == 1
    assert Decimal(str(dash_b["total_sales"])) == Decimal("200.00")
    assert dash_b["total_items_sold"] == 1

    # 7. Check Admin global dashboard:
    # Combined: 3 products, 2 active, 3 variants, 1 confirmed order, $500 total sales, 3 items sold
    dash_admin = (await async_client.get("/api/v1/seller/dashboard", headers=headers_admin)).json()
    assert dash_admin["total_products"] == 3
    assert dash_admin["active_products"] == 2
    assert dash_admin["total_variants"] == 3
    assert dash_admin["confirmed_orders"] == 1
    assert Decimal(str(dash_admin["total_sales"])) == Decimal("500.00")
    assert dash_admin["total_items_sold"] == 3

    # Admin filtering by seller_a
    dash_admin_a = (
        await async_client.get(f"/api/v1/seller/dashboard?seller_id={seller_a.id}", headers=headers_admin)
    ).json()
    assert Decimal(str(dash_admin_a["total_sales"])) == Decimal("300.00")


@pytest.mark.asyncio
async def test_seller_products_crud_and_cross_seller_forbidden(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """CRUD own products; verify cross-seller access is denied (403)."""
    seller_a = await create_user_helper(email="prod_a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="prod_b@example.com", role=UserRole.SELLER)
    admin = await create_user_helper(email="prod_adm@example.com", role=UserRole.ADMIN)

    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)
    headers_admin = auth_headers_helper(admin)

    # 1. Seller A creates product
    create_res = await async_client.post(
        "/api/v1/seller/products",
        json={
            "name": "Velvet Evening Gown",
            "slug": "velvet-evening-gown",
            "base_price": "350.00",
            "status": "ACTIVE",
        },
        headers=headers_a,
    )
    assert create_res.status_code == 201
    prod_id = create_res.json()["id"]
    assert create_res.json()["seller_id"] == str(seller_a.id)

    # 2. Seller A can GET and PATCH own product
    get_res = await async_client.get(f"/api/v1/seller/products/{prod_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Velvet Evening Gown"

    patch_res = await async_client.patch(
        f"/api/v1/seller/products/{prod_id}",
        json={"base_price": "380.00"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["base_price"] == "380.00"

    # 3. Security: Seller B cannot GET Seller A product
    b_get = await async_client.get(f"/api/v1/seller/products/{prod_id}", headers=headers_b)
    assert b_get.status_code == 403

    # 4. Security: Seller B cannot PATCH Seller A product
    b_patch = await async_client.patch(
        f"/api/v1/seller/products/{prod_id}",
        json={"base_price": "10.00"},
        headers=headers_b,
    )
    assert b_patch.status_code == 403

    # 5. Security: Seller B cannot DELETE Seller A product
    b_del = await async_client.delete(f"/api/v1/seller/products/{prod_id}", headers=headers_b)
    assert b_del.status_code == 403

    # 6. Admin can GET, PATCH, and view Seller A product
    adm_get = await async_client.get(f"/api/v1/seller/products/{prod_id}", headers=headers_admin)
    assert adm_get.status_code == 200

    adm_patch = await async_client.patch(
        f"/api/v1/seller/products/{prod_id}",
        json={"name": "Velvet Evening Gown - Admin Edit"},
        headers=headers_admin,
    )
    assert adm_patch.status_code == 200
    assert adm_patch.json()["name"] == "Velvet Evening Gown - Admin Edit"


@pytest.mark.asyncio
async def test_seller_ownership_spoofing_prevented(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Passing a forged seller_id in request body or query cannot reassign ownership."""
    seller_a = await create_user_helper(email="seller_sp1@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="seller_sp2@example.com", role=UserRole.SELLER)

    # Seller A sends payload with seller_b id
    res = await async_client.post(
        "/api/v1/seller/products",
        json={
            "name": "Spoofed Ownership Jacket",
            "base_price": "299.00",
            "seller_id": str(seller_b.id),
        },
        headers=auth_headers_helper(seller_a),
    )
    assert res.status_code == 201
    # Ownership MUST be seller_a, not seller_b
    assert res.json()["seller_id"] == str(seller_a.id)


@pytest.mark.asyncio
async def test_seller_variant_crud_and_security(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Seller manages variants for own product; cross-seller operations are rejected."""
    seller_a = await create_user_helper(email="var_a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="var_b@example.com", role=UserRole.SELLER)

    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)

    prod = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Pleated Skirt", "base_price": "90.00"},
        headers=headers_a,
    )
    prod_id = prod.json()["id"]

    # 1. Seller A creates variant
    v_res = await async_client.post(
        f"/api/v1/seller/products/{prod_id}/variants",
        json={"sku": "SKIRT-BLK-S", "price": "90.00", "size": "S", "color": "Black"},
        headers=headers_a,
    )
    assert v_res.status_code == 201
    var_id = v_res.json()["id"]

    # 2. Seller B cannot create variant on Seller A product
    b_create_var = await async_client.post(
        f"/api/v1/seller/products/{prod_id}/variants",
        json={"sku": "SKIRT-BLK-M", "price": "90.00"},
        headers=headers_b,
    )
    assert b_create_var.status_code == 403

    # 3. Seller B cannot PATCH Seller A variant
    b_patch_var = await async_client.patch(
        f"/api/v1/seller/products/{prod_id}/variants/{var_id}",
        json={"price": "1.00"},
        headers=headers_b,
    )
    assert b_patch_var.status_code == 403

    # 4. Seller B cannot DELETE Seller A variant
    b_del_var = await async_client.delete(
        f"/api/v1/seller/products/{prod_id}/variants/{var_id}",
        headers=headers_b,
    )
    assert b_del_var.status_code == 403

    # 5. Direct variant endpoint security
    b_direct_patch = await async_client.patch(
        f"/api/v1/seller/variants/{var_id}",
        json={"price": "1.00"},
        headers=headers_b,
    )
    assert b_direct_patch.status_code == 403

    # 6. Price validation: negative price or compare_at_price < price
    val_neg = await async_client.patch(
        f"/api/v1/seller/variants/{var_id}",
        json={"price": "-10.00"},
        headers=headers_a,
    )
    assert val_neg.status_code == 422

    val_comp = await async_client.patch(
        f"/api/v1/seller/variants/{var_id}",
        json={"price": "100.00", "compare_at_price": "50.00"},
        headers=headers_a,
    )
    assert val_comp.status_code == 422


@pytest.mark.asyncio
async def test_seller_inventory_management_and_reservation_safety(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Seller manages inventory; cross-seller access denied; cannot reduce below reserved."""
    seller_a = await create_user_helper(email="inv_a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="inv_b@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="inv_cust@example.com", role=UserRole.CUSTOMER)

    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)
    headers_cust = auth_headers_helper(customer)

    # 1. Seller A creates product + variant
    p = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Wool Cardigan", "base_price": "140.00", "status": "ACTIVE"},
        headers=headers_a,
    )
    p_id = p.json()["id"]

    v = await async_client.post(
        f"/api/v1/seller/products/{p_id}/variants",
        json={"sku": "CARD-NAVY-M", "price": "140.00"},
        headers=headers_a,
    )
    v_id = v.json()["id"]

    # 2. Seller A sets initial stock to 10
    set_res = await async_client.patch(
        f"/api/v1/seller/inventory/{v_id}",
        json={"quantity_on_hand": 10, "low_stock_threshold": 3},
        headers=headers_a,
    )
    assert set_res.status_code == 200
    assert set_res.json()["quantity_on_hand"] == 10
    assert set_res.json()["quantity_available"] == 10

    # 3. Seller B cannot view or modify Seller A inventory
    b_view = await async_client.get(f"/api/v1/seller/inventory/{v_id}", headers=headers_b)
    assert b_view.status_code == 403

    b_set = await async_client.patch(
        f"/api/v1/seller/inventory/{v_id}",
        json={"quantity_on_hand": 100},
        headers=headers_b,
    )
    assert b_set.status_code == 403

    b_adj = await async_client.post(
        f"/api/v1/seller/inventory/{v_id}/adjust",
        json={"adjustment": 5},
        headers=headers_b,
    )
    assert b_adj.status_code == 403

    # 4. Customer reserves 4 units via checkout
    await async_client.post("/api/v1/cart/items", json={"variant_id": v_id, "quantity": 4}, headers=headers_cust)
    await async_client.post("/api/v1/checkout", headers=headers_cust)

    # Check Seller A inventory view
    inv_check = (await async_client.get(f"/api/v1/seller/inventory/{v_id}", headers=headers_a)).json()
    assert inv_check["quantity_on_hand"] == 10
    assert inv_check["quantity_reserved"] == 4
    assert inv_check["quantity_available"] == 6

    # 5. Invariant protection: Seller A CANNOT reduce stock below reserved quantity (4)
    inv_viol = await async_client.patch(
        f"/api/v1/seller/inventory/{v_id}",
        json={"quantity_on_hand": 3},
        headers=headers_a,
    )
    assert inv_viol.status_code == 400
    assert "reserved" in inv_viol.json()["detail"].lower()

    adj_viol = await async_client.post(
        f"/api/v1/seller/inventory/{v_id}/adjust",
        json={"adjustment": -7},
        headers=headers_a,
    )
    assert adj_viol.status_code == 400

    # 6. Seller A can adjust valid delta
    adj_ok = await async_client.post(
        f"/api/v1/seller/inventory/{v_id}/adjust",
        json={"adjustment": 5, "reason": "Restock"},
        headers=headers_a,
    )
    assert adj_ok.status_code == 200
    assert adj_ok.json()["quantity_on_hand"] == 15
    assert adj_ok.json()["quantity_available"] == 11


@pytest.mark.asyncio
async def test_seller_orders_visibility_and_isolation(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """
    Multi-vendor order: customer buys from Seller A and Seller B.
    Seller A sees only Seller A items.
    Seller B sees only Seller B items.
    Customer sees complete order.
    Unrelated orders return 404 for seller.
    """
    seller_a = await create_user_helper(email="ord_seller_a@example.com", role=UserRole.SELLER)
    seller_b = await create_user_helper(email="ord_seller_b@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="ord_cust@example.com", role=UserRole.CUSTOMER)

    headers_a = auth_headers_helper(seller_a)
    headers_b = auth_headers_helper(seller_b)
    headers_cust = auth_headers_helper(customer)

    # 1. Seller A creates Product A ($120.00)
    p_a = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Seller A Blazer", "base_price": "120.00", "status": "ACTIVE"},
        headers=headers_a,
    )
    v_a = await async_client.post(
        f"/api/v1/seller/products/{p_a.json()['id']}/variants",
        json={"sku": "BLZ-A-38", "price": "120.00"},
        headers=headers_a,
    )
    va_id = v_a.json()["id"]
    await async_client.patch(f"/api/v1/seller/inventory/{va_id}", json={"quantity_on_hand": 10}, headers=headers_a)

    # 2. Seller B creates Product B ($75.00)
    p_b = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Seller B Scarf", "base_price": "75.00", "status": "ACTIVE"},
        headers=headers_b,
    )
    v_b = await async_client.post(
        f"/api/v1/seller/products/{p_b.json()['id']}/variants",
        json={"sku": "SCF-B-OS", "price": "75.00"},
        headers=headers_b,
    )
    vb_id = v_b.json()["id"]
    await async_client.patch(f"/api/v1/seller/inventory/{vb_id}", json={"quantity_on_hand": 10}, headers=headers_b)

    # 3. Customer checks out both: 2 of A ($240) + 1 of B ($75) = $315
    await async_client.post("/api/v1/cart/items", json={"variant_id": va_id, "quantity": 2}, headers=headers_cust)
    await async_client.post("/api/v1/cart/items", json={"variant_id": vb_id, "quantity": 1}, headers=headers_cust)
    checkout = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout.status_code == 201
    order_id = checkout.json()["id"]

    # 4. Customer verifies seeing full order (both items, total 315)
    cust_ord = (await async_client.get(f"/api/v1/orders/{order_id}", headers=headers_cust)).json()
    assert len(cust_ord["items"]) == 2
    assert Decimal(str(cust_ord["total"])) == Decimal("315.00")

    # 5. Seller A views orders
    seller_a_orders = (await async_client.get("/api/v1/seller/orders", headers=headers_a)).json()
    assert len(seller_a_orders) == 1
    ord_a = seller_a_orders[0]
    assert ord_a["id"] == order_id
    assert len(ord_a["items"]) == 1
    assert ord_a["items"][0]["sku"] == "BLZ-A-38"
    assert ord_a["items"][0]["quantity"] == 2
    assert Decimal(str(ord_a["seller_subtotal"])) == Decimal("240.00")
    assert ord_a["seller_total_quantity"] == 2

    # Seller A views specific order
    single_a = (await async_client.get(f"/api/v1/seller/orders/{order_id}", headers=headers_a)).json()
    assert len(single_a["items"]) == 1
    assert single_a["items"][0]["sku"] == "BLZ-A-38"

    # 6. Seller B views orders
    seller_b_orders = (await async_client.get("/api/v1/seller/orders", headers=headers_b)).json()
    assert len(seller_b_orders) == 1
    ord_b = seller_b_orders[0]
    assert ord_b["id"] == order_id
    assert len(ord_b["items"]) == 1
    assert ord_b["items"][0]["sku"] == "SCF-B-OS"
    assert ord_b["items"][0]["quantity"] == 1
    assert Decimal(str(ord_b["seller_subtotal"])) == Decimal("75.00")
    assert ord_b["seller_total_quantity"] == 1

    # 7. Seller C (no items in order) gets 404 Not Found on this order
    seller_c = await create_user_helper(email="ord_seller_c@example.com", role=UserRole.SELLER)
    c_res = await async_client.get(f"/api/v1/seller/orders/{order_id}", headers=auth_headers_helper(seller_c))
    assert c_res.status_code == 404

    # Seller C list orders returns empty
    c_list = await async_client.get("/api/v1/seller/orders", headers=auth_headers_helper(seller_c))
    assert len(c_list.json()) == 0


@pytest.mark.asyncio
async def test_seller_safe_archive_product_on_delete_with_orders(
    async_client: AsyncClient,
    create_user_helper,
    auth_headers_helper,
):
    """Deleting a product that has historical orders archives it safely without breaking snapshots."""
    seller = await create_user_helper(email="del_arch_seller@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="del_arch_cust@example.com", role=UserRole.CUSTOMER)

    headers_seller = auth_headers_helper(seller)
    headers_cust = auth_headers_helper(customer)

    # 1. Create product & variant
    p = await async_client.post(
        "/api/v1/seller/products",
        json={"name": "Archive Test Coat", "base_price": "250.00", "status": "ACTIVE"},
        headers=headers_seller,
    )
    p_id = p.json()["id"]

    v = await async_client.post(
        f"/api/v1/seller/products/{p_id}/variants",
        json={"sku": "COAT-ARCH-L", "price": "250.00"},
        headers=headers_seller,
    )
    v_id = v.json()["id"]

    await async_client.patch(f"/api/v1/seller/inventory/{v_id}", json={"quantity_on_hand": 5}, headers=headers_seller)

    # 2. Customer orders the coat
    await async_client.post("/api/v1/cart/items", json={"variant_id": v_id, "quantity": 1}, headers=headers_cust)
    checkout = await async_client.post("/api/v1/checkout", headers=headers_cust)
    assert checkout.status_code == 201

    # 3. Seller deletes the product
    del_res = await async_client.delete(f"/api/v1/seller/products/{p_id}", headers=headers_seller)
    assert del_res.status_code == 204

    # 4. Verify product was archived safely (not hard deleted)
    prod_check = (await async_client.get(f"/api/v1/seller/products/{p_id}", headers=headers_seller)).json()
    assert prod_check["status"] == "ARCHIVED"
    assert prod_check["is_active"] is False

    # 5. Customer order history still contains the snapshot and variant info intact
    cust_orders = (await async_client.get("/api/v1/orders", headers=headers_cust)).json()
    assert len(cust_orders) == 1
    assert cust_orders[0]["items"][0]["sku"] == "COAT-ARCH-L"
    assert cust_orders[0]["items"][0]["product_name"] == "Archive Test Coat"
