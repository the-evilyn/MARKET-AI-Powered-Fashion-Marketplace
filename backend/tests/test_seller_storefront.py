import io
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.storage import StorageService
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Brand, Category, Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.seller.enums import StoreStatus
from app.modules.seller.models import Store
from app.modules.seller.service import SellerService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 30
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
INVALID_BYTES = b"This is plain text, not an image header."


@pytest.fixture
async def seller_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"seller_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed_pw",
        first_name="Jean",
        last_name="Gaultier",
        role=UserRole.SELLER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def seller_user_two(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"seller2_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed_pw",
        first_name="Coco",
        last_name="Chanel",
        role=UserRole.SELLER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def customer_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"customer_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed_pw",
        first_name="Alice",
        last_name="Buyer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def seller_headers(seller_user: User, auth_headers_helper):
    return auth_headers_helper(seller_user)


@pytest.fixture
def seller_two_headers(seller_user_two: User, auth_headers_helper):
    return auth_headers_helper(seller_user_two)


@pytest.fixture
def customer_headers(customer_user: User, auth_headers_helper):
    return auth_headers_helper(customer_user)


# ==============================================================================
# Mandatory Test Cases 1-20
# ==============================================================================

@pytest.mark.anyio
async def test_seller_can_get_own_store(
    async_client: AsyncClient,
    seller_user: User,
    seller_headers: dict,
):
    """1. Seller can retrieve their store, auto-provisioned lazily."""
    response = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == str(seller_user.id)
    assert "Jean Gaultier" in data["store_name"]
    assert data["status"] == "ACTIVE"
    assert data["is_verified"] is False
    assert "slug" in data


@pytest.mark.anyio
async def test_seller_can_update_own_store(
    async_client: AsyncClient,
    seller_headers: dict,
):
    """2. Seller can update store_name, bio, contact_email, contact_phone."""
    payload = {
        "store_name": "Maison Sartoriale",
        "bio": "Haute couture urbaine et éco-responsable.",
        "contact_email": "concierge@sartoriale.fr",
        "contact_phone": "+33140205000",
    }
    response = await async_client.patch("/api/v1/seller/profile", headers=seller_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == "Maison Sartoriale"
    assert data["bio"] == "Haute couture urbaine et éco-responsable."
    assert data["contact_email"] == "concierge@sartoriale.fr"
    assert data["contact_phone"] == "+33140205000"


@pytest.mark.anyio
async def test_seller_cannot_modify_status(
    async_client: AsyncClient,
    seller_headers: dict,
):
    """3. Seller cannot modify internal Store status (extra fields rejected)."""
    response = await async_client.patch(
        "/api/v1/seller/profile",
        headers=seller_headers,
        json={"status": "SUSPENDED"},
    )
    assert response.status_code == 422  # Pydantic extra="forbid"


@pytest.mark.anyio
async def test_seller_cannot_modify_is_verified(
    async_client: AsyncClient,
    seller_headers: dict,
):
    """4. Seller cannot tamper with is_verified flag."""
    response = await async_client.patch(
        "/api/v1/seller/profile",
        headers=seller_headers,
        json={"is_verified": True},
    )
    assert response.status_code == 422  # Pydantic extra="forbid"


@pytest.mark.anyio
async def test_customer_cannot_access_seller_profile(
    async_client: AsyncClient,
    customer_headers: dict,
):
    """5. Customer role cannot access private seller store endpoint."""
    response = await async_client.get("/api/v1/seller/profile", headers=customer_headers)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_unauthenticated_seller_endpoint_rejected(
    async_client: AsyncClient,
):
    """6. Unauthenticated requests to seller endpoints are rejected with 401."""
    response = await async_client.get("/api/v1/seller/profile")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_duplicate_store_name_rejected(
    async_client: AsyncClient,
    seller_headers: dict,
    seller_two_headers: dict,
):
    """7. Two sellers cannot claim the exact same store name."""
    await async_client.patch(
        "/api/v1/seller/profile",
        headers=seller_headers,
        json={"store_name": "Luxe Unique Studio"},
    )

    conflict_res = await async_client.patch(
        "/api/v1/seller/profile",
        headers=seller_two_headers,
        json={"store_name": "Luxe Unique Studio"},
    )
    assert conflict_res.status_code == 409


@pytest.mark.anyio
async def test_public_store_works_without_jwt(
    async_client: AsyncClient,
    seller_headers: dict,
):
    """8. Public store endpoint resolves without any Authorization header."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    pub_res = await async_client.get(f"/api/v1/stores/{slug}")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["slug"] == slug
    assert "store_name" in pub_data


@pytest.mark.anyio
async def test_unknown_slug_returns_404(
    async_client: AsyncClient,
):
    """9. Querying a non-existent slug returns 404."""
    response = await async_client.get("/api/v1/stores/completely-unknown-slug-xyz")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_suspended_store_returns_404(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
):
    """10. Stores in SUSPENDED status return 404 on public endpoints."""
    store = await SellerService.get_or_create_store(db_session, seller_user.id)
    store.status = StoreStatus.SUSPENDED
    await db_session.commit()

    response = await async_client.get(f"/api/v1/stores/{store.slug}")
    assert response.status_code == 404

    prod_res = await async_client.get(f"/api/v1/stores/{store.slug}/products")
    assert prod_res.status_code == 404


@pytest.mark.anyio
async def test_sensitive_seller_data_is_not_exposed(
    async_client: AsyncClient,
    seller_headers: dict,
    seller_user: User,
):
    """11. Public store JSON never leaks seller_id, password_hash, user email or private account info."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    pub_res = await async_client.get(f"/api/v1/stores/{slug}")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()

    # Assert forbidden sensitive keys
    assert "seller_id" not in pub_data
    assert "password_hash" not in pub_data
    assert "first_name" not in pub_data
    assert "last_name" not in pub_data
    assert "status" not in pub_data
    # Contact email is dedicated business field, never private user account email
    assert pub_data.get("contact_email") != seller_user.email


@pytest.mark.anyio
async def test_only_active_products_are_returned(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
    seller_headers: dict,
):
    """12. Only ACTIVE and is_active=True products are returned on public store products endpoint."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    # Create active product
    p_active = Product(
        id=uuid.uuid4(),
        seller_id=seller_user.id,
        name="Active Silk Scarf",
        slug=f"silk-scarf-{uuid.uuid4().hex[:6]}",
        base_price=Decimal("89.00"),
        status=ProductStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(p_active)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/stores/{slug}/products")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(i["id"] == str(p_active.id) for i in items)


@pytest.mark.anyio
async def test_draft_products_hidden(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
    seller_headers: dict,
):
    """13. DRAFT products are hidden from public store products endpoint."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    p_draft = Product(
        id=uuid.uuid4(),
        seller_id=seller_user.id,
        name="Draft Leather Jacket",
        slug=f"draft-jacket-{uuid.uuid4().hex[:6]}",
        base_price=Decimal("450.00"),
        status=ProductStatus.DRAFT,
        is_active=True,
    )
    db_session.add(p_draft)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/stores/{slug}/products")
    assert res.status_code == 200
    items = res.json()["items"]
    assert not any(i["id"] == str(p_draft.id) for i in items)


@pytest.mark.anyio
async def test_archived_products_hidden(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
    seller_headers: dict,
):
    """14. ARCHIVED products are hidden from public store products endpoint."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    p_archived = Product(
        id=uuid.uuid4(),
        seller_id=seller_user.id,
        name="Archived Wool Coat",
        slug=f"archived-coat-{uuid.uuid4().hex[:6]}",
        base_price=Decimal("320.00"),
        status=ProductStatus.ARCHIVED,
        is_active=True,
    )
    db_session.add(p_archived)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/stores/{slug}/products")
    assert res.status_code == 200
    items = res.json()["items"]
    assert not any(i["id"] == str(p_archived.id) for i in items)


@pytest.mark.anyio
async def test_products_from_another_seller_never_leak(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
    seller_user_two: User,
    seller_headers: dict,
):
    """15. Products owned by seller B never leak into store A's catalog."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug_a = setup_res.json()["slug"]

    # Product owned by seller two
    p_other = Product(
        id=uuid.uuid4(),
        seller_id=seller_user_two.id,
        name="Seller Two Handbag",
        slug=f"seller2-bag-{uuid.uuid4().hex[:6]}",
        base_price=Decimal("190.00"),
        status=ProductStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(p_other)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/stores/{slug_a}/products")
    assert res.status_code == 200
    items = res.json()["items"]
    assert not any(i["id"] == str(p_other.id) for i in items)


@pytest.mark.anyio
async def test_pagination_works(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seller_user: User,
    seller_headers: dict,
):
    """16. Pagination query parameters limit items correctly."""
    setup_res = await async_client.get("/api/v1/seller/profile", headers=seller_headers)
    slug = setup_res.json()["slug"]

    # Add 3 active items
    for idx in range(3):
        p = Product(
            id=uuid.uuid4(),
            seller_id=seller_user.id,
            name=f"Paginated Item {idx}",
            slug=f"paginated-item-{idx}-{uuid.uuid4().hex[:6]}",
            base_price=Decimal("50.00"),
            status=ProductStatus.ACTIVE,
            is_active=True,
        )
        db_session.add(p)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/stores/{slug}/products?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 3


@pytest.mark.anyio
async def test_valid_image_upload_works(
    async_client: AsyncClient,
    seller_headers: dict,
    monkeypatch,
):
    """17. Valid image upload sets URL and object_key."""
    def mock_upload(data, object_key, content_type="image/jpeg", bucket_name=None):
        return f"http://localhost:9000/fashion-media/{object_key}"

    monkeypatch.setattr(StorageService, "upload_file", staticmethod(mock_upload))

    files = {"file": ("logo.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = await async_client.post("/api/v1/seller/profile/logo", headers=seller_headers, files=files)
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "logo" in data["object_key"]


@pytest.mark.anyio
async def test_invalid_image_rejected(
    async_client: AsyncClient,
    seller_headers: dict,
):
    """18. Non-image bytes or invalid MIME are rejected with 400 Bad Request."""
    files = {"file": ("fake.jpg", io.BytesIO(INVALID_BYTES), "image/jpeg")}
    response = await async_client.post("/api/v1/seller/profile/logo", headers=seller_headers, files=files)
    assert response.status_code == 400


@pytest.mark.anyio
async def test_replacement_deletes_old_object(
    async_client: AsyncClient,
    seller_headers: dict,
    monkeypatch,
):
    """19. Replacing banner image deletes the previous MinIO object key."""
    deleted_keys = []

    def mock_upload(data, object_key, content_type="image/png", bucket_name=None):
        return f"http://localhost:9000/fashion-media/{object_key}"

    def mock_delete(object_key, bucket_name=None):
        deleted_keys.append(object_key)
        return True

    monkeypatch.setattr(StorageService, "upload_file", staticmethod(mock_upload))
    monkeypatch.setattr(StorageService, "delete_file", staticmethod(mock_delete))

    # First banner upload
    f1 = {"file": ("banner1.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    r1 = await async_client.post("/api/v1/seller/profile/banner", headers=seller_headers, files=f1)
    assert r1.status_code == 200
    first_key = r1.json()["object_key"]

    # Second banner upload replacing the first
    f2 = {"file": ("banner2.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    r2 = await async_client.post("/api/v1/seller/profile/banner", headers=seller_headers, files=f2)
    assert r2.status_code == 200
    second_key = r2.json()["object_key"]

    assert first_key != second_key
    assert first_key in deleted_keys


@pytest.mark.anyio
async def test_lazy_provisioning_does_not_create_duplicate_stores(
    db_session: AsyncSession,
    seller_user: User,
):
    """20. Multiple consecutive get_or_create_store calls return the exact same store entity."""
    store_first = await SellerService.get_or_create_store(db_session, seller_user.id)
    store_second = await SellerService.get_or_create_store(db_session, seller_user.id)

    assert store_first.id == store_second.id
    assert store_first.slug == store_second.slug

    # Verify directly in DB that count is 1
    stmt = select(Store).where(Store.seller_id == seller_user.id)
    all_stores = (await db_session.execute(stmt)).scalars().all()
    assert len(all_stores) == 1
