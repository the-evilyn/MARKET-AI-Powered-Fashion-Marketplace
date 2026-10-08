import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
)
from app.modules.inventory.schemas import (
    InventoryAdjustRequest,
    InventoryUpdate,
)
from app.modules.orders.enums import OrderStatus
from app.modules.seller.schemas import (
    SellerDashboardResponse,
    SellerFulfillmentRequest,
    SellerInventoryItemResponse,
    SellerOrderResponse,
    SellerProfileResponse,
    SellerProfileUpdate,
    StoreMediaUploadResponse,
)
from app.modules.seller.service import SellerService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/seller", tags=["Seller Operations"])


def resolve_seller_scope(current_user: User, admin_seller_id: Optional[uuid.UUID] = None) -> Optional[uuid.UUID]:
    """
    Ensure SELLER can never specify another seller_id.
    ADMIN can pass seller_id to filter or omit for global view.
    """
    if current_user.role == UserRole.SELLER:
        return current_user.id
    return admin_seller_id


# ==============================================================================
# Dashboard KPIs
# ==============================================================================

@router.get("/dashboard", response_model=SellerDashboardResponse, summary="Get seller dashboard KPIs")
async def get_seller_dashboard(
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Admin-only filter by seller ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerDashboardResponse:
    """Retrieve seller KPI dashboard metrics with strict ownership boundary enforcement."""
    effective_seller_id = resolve_seller_scope(current_user, seller_id)
    return await SellerService.get_dashboard_kpis(db, effective_seller_id)


# ==============================================================================
# Products Management
# ==============================================================================

@router.get("/products", response_model=List[ProductResponse], summary="List seller products")
async def list_seller_products(
    status_filter: Optional[ProductStatus] = Query(default=None, alias="status"),
    is_active: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Admin-only filter by seller ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> List[ProductResponse]:
    """List products owned by the authenticated seller (or all for admin)."""
    effective_seller_id = resolve_seller_scope(current_user, seller_id)
    products = await SellerService.list_products(
        db=db,
        seller_id=effective_seller_id,
        status_filter=status_filter,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [ProductResponse.model_validate(p) for p in products]


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create seller product",
)
async def create_seller_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductResponse:
    """Create a new product owned by the authenticated seller."""
    product = await SellerService.create_product(db, seller_id=current_user.id, payload=payload)
    return ProductResponse.model_validate(product)


@router.get("/products/{product_id}", response_model=ProductDetailResponse, summary="Get seller product details")
async def get_seller_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductDetailResponse:
    """Retrieve product details with ownership verification."""
    effective_seller_id = resolve_seller_scope(current_user)
    product = await SellerService.get_product_by_id(db, product_id, effective_seller_id)
    return ProductDetailResponse.model_validate(product)


@router.patch("/products/{product_id}", response_model=ProductResponse, summary="Update seller product")
async def update_seller_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductResponse:
    """Update product details with ownership verification."""
    effective_seller_id = resolve_seller_scope(current_user)
    updated = await SellerService.update_product(db, product_id, effective_seller_id, payload)
    return ProductResponse.model_validate(updated)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or safe-archive seller product",
)
async def delete_seller_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete or safe-archive product depending on order history existence."""
    effective_seller_id = resolve_seller_scope(current_user)
    await SellerService.delete_product(db, product_id, effective_seller_id)


# ==============================================================================
# Variant Management
# ==============================================================================

@router.get(
    "/products/{product_id}/variants",
    response_model=List[ProductVariantResponse],
    summary="List variants of seller product",
)
async def list_seller_variants(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> List[ProductVariantResponse]:
    """List SKU variants for a product owned by seller."""
    effective_seller_id = resolve_seller_scope(current_user)
    variants = await SellerService.list_variants(db, product_id, effective_seller_id)
    return [ProductVariantResponse.model_validate(v) for v in variants]


@router.post(
    "/products/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create variant for seller product",
)
async def create_seller_variant(
    product_id: uuid.UUID,
    payload: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductVariantResponse:
    """Create a new SKU variant for a product owned by seller."""
    effective_seller_id = resolve_seller_scope(current_user)
    variant = await SellerService.create_variant(db, product_id, effective_seller_id, payload)
    return ProductVariantResponse.model_validate(variant)


@router.patch(
    "/products/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Update variant of seller product",
)
async def update_seller_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductVariantResponse:
    """Update variant belonging to seller product."""
    effective_seller_id = resolve_seller_scope(current_user)
    variant = await SellerService.update_variant(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
        payload=payload,
        product_id=product_id,
    )
    return ProductVariantResponse.model_validate(variant)


@router.delete(
    "/products/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or safe-deactivate variant of seller product",
)
async def delete_seller_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete or safe-deactivate variant belonging to seller product."""
    effective_seller_id = resolve_seller_scope(current_user)
    await SellerService.delete_variant(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
        product_id=product_id,
    )


@router.patch(
    "/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Update variant by ID directly",
)
async def update_seller_variant(
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductVariantResponse:
    """Update variant directly with ownership verification."""
    effective_seller_id = resolve_seller_scope(current_user)
    variant = await SellerService.update_variant(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
        payload=payload,
    )
    return ProductVariantResponse.model_validate(variant)


@router.delete(
    "/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or deactivate variant by ID directly",
)
async def delete_seller_variant(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete or safe-deactivate variant directly with ownership verification."""
    effective_seller_id = resolve_seller_scope(current_user)
    await SellerService.delete_variant(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
    )


# ==============================================================================
# Inventory Management
# ==============================================================================

@router.get("/inventory", response_model=List[SellerInventoryItemResponse], summary="List seller inventory")
async def list_seller_inventory(
    low_stock_only: bool = Query(default=False, description="Filter items at or below low stock threshold"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Admin-only filter by seller ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> List[SellerInventoryItemResponse]:
    """List inventory items for seller variants with available stock and low stock indicators."""
    effective_seller_id = resolve_seller_scope(current_user, seller_id)
    return await SellerService.list_inventory(
        db=db,
        seller_id=effective_seller_id,
        low_stock_only=low_stock_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/inventory/{variant_id}",
    response_model=SellerInventoryItemResponse,
    summary="Get seller variant inventory details",
)
async def get_seller_inventory_item(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerInventoryItemResponse:
    """Retrieve full inventory details for a SKU variant owned by seller."""
    effective_seller_id = resolve_seller_scope(current_user)
    return await SellerService.get_inventory_item(db, variant_id, effective_seller_id)


@router.patch(
    "/inventory/{variant_id}",
    response_model=SellerInventoryItemResponse,
    summary="Update seller variant stock level or threshold",
)
async def update_seller_inventory(
    variant_id: uuid.UUID,
    payload: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerInventoryItemResponse:
    """Set absolute stock quantity or threshold for seller variant."""
    effective_seller_id = resolve_seller_scope(current_user)
    return await SellerService.set_stock(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
        quantity_on_hand=payload.quantity_on_hand,
        low_stock_threshold=payload.low_stock_threshold,
    )


@router.post(
    "/inventory/{variant_id}/adjust",
    response_model=SellerInventoryItemResponse,
    summary="Adjust seller variant stock on hand",
)
async def adjust_seller_inventory(
    variant_id: uuid.UUID,
    payload: InventoryAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerInventoryItemResponse:
    """Adjust stock on hand by signed delta for seller variant."""
    effective_seller_id = resolve_seller_scope(current_user)
    return await SellerService.adjust_stock(
        db=db,
        variant_id=variant_id,
        seller_id=effective_seller_id,
        adjustment=payload.adjustment,
        reason=payload.reason,
    )


# ==============================================================================
# Seller Order Visibility
# ==============================================================================

@router.get("/orders", response_model=List[SellerOrderResponse], summary="List seller orders")
async def list_seller_orders(
    status_filter: Optional[OrderStatus] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Admin-only filter by seller ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> List[SellerOrderResponse]:
    """
    List orders containing items belonging to the seller.
    Only items belonging to this seller are included in the response.
    """
    effective_seller_id = resolve_seller_scope(current_user, seller_id)
    return await SellerService.list_orders(
        db=db,
        seller_id=effective_seller_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/orders/{order_id}", response_model=SellerOrderResponse, summary="Get seller order detail")
async def get_seller_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerOrderResponse:
    """
    Retrieve order details filtered strictly to the authenticated seller's items.
    Returns 404 if the order does not contain items belonging to this seller.
    """
    effective_seller_id = resolve_seller_scope(current_user)
    return await SellerService.get_order(db, order_id, effective_seller_id)


@router.patch(
    "/orders/{order_id}/fulfillment",
    response_model=SellerOrderResponse,
    summary="Update seller order fulfillment status, carrier, and tracking number",
)
async def update_seller_order_fulfillment(
    order_id: uuid.UUID,
    payload: SellerFulfillmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> SellerOrderResponse:
    """
    Update vendor fulfillment state (e.g. PROCESSING, SHIPPED, DELIVERED), carrier, and tracking number.
    Strictly restricted to the seller's own sub-order.
    """
    effective_seller_id = resolve_seller_scope(current_user)
    return await SellerService.update_fulfillment(
        db=db,
        sub_order_id=order_id,
        seller_id=effective_seller_id,
        new_status=payload.status,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
    )


# ==============================================================================
# Store Profile Management (Phase 9B.1)
# ==============================================================================

@router.get(
    "/profile",
    response_model=SellerProfileResponse,
    summary="Get authenticated seller's store profile",
)
async def get_seller_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER)),
) -> SellerProfileResponse:
    """Retrieve seller's store profile. Lazily provisions store if not yet created."""
    store = await SellerService.get_or_create_store(db, current_user.id)
    return SellerProfileResponse.model_validate(store)


@router.patch(
    "/profile",
    response_model=SellerProfileResponse,
    summary="Update authenticated seller's store profile",
)
async def update_seller_profile(
    payload: SellerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER)),
) -> SellerProfileResponse:
    """Update seller's store profile (name, slug, bio, contact email, contact phone)."""
    updated_store = await SellerService.update_store_profile(db, current_user.id, payload)
    return SellerProfileResponse.model_validate(updated_store)


@router.post(
    "/profile/logo",
    response_model=StoreMediaUploadResponse,
    summary="Upload store logo image",
)
async def upload_seller_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER)),
) -> StoreMediaUploadResponse:
    """Upload new store logo image (max 5MB, JPEG/PNG/WebP, magic bytes)."""
    file_content = await file.read()
    return await SellerService.upload_store_logo(
        db=db,
        seller_id=current_user.id,
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type,
    )


@router.post(
    "/profile/banner",
    response_model=StoreMediaUploadResponse,
    summary="Upload store banner image",
)
async def upload_seller_banner(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER)),
) -> StoreMediaUploadResponse:
    """Upload new store banner image (max 10MB, JPEG/PNG/WebP, magic bytes)."""
    file_content = await file.read()
    return await SellerService.upload_store_banner(
        db=db,
        seller_id=current_user.id,
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type,
    )

