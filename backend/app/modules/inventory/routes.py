import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.inventory.schemas import (
    InventoryAdjustRequest,
    InventoryResponse,
    InventoryUpdate,
    PublicVariantStockResponse,
)
from app.modules.inventory.service import InventoryService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


async def get_variant_and_check_ownership(
    db: AsyncSession,
    variant_id: uuid.UUID,
    current_user: User,
) -> tuple[ProductVariant, Product]:
    """Retrieve variant and parent product, enforcing seller ownership or ADMIN role."""
    stmt = (
        select(ProductVariant)
        .where(ProductVariant.id == variant_id)
        .options(selectinload(ProductVariant.product))
    )
    res = await db.execute(stmt)
    variant = res.scalar_one_or_none()
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id '{variant_id}' not found.",
        )
    product = variant.product
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product for variant '{variant_id}' not found.",
        )

    if current_user.role != UserRole.ADMIN and product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage inventory for this product.",
        )
    return variant, product


@router.get("", response_model=List[InventoryResponse], summary="List inventory items")
async def list_inventory(
    low_stock_only: bool = Query(default=False, description="Filter items at or below low stock threshold"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Admin-only filter by seller ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> List[InventoryResponse]:
    """
    List inventory items.
    Sellers only see inventory for their own products.
    Admins can see all inventory records or filter by a specific seller.
    """
    effective_seller_id: Optional[uuid.UUID] = current_user.id
    if current_user.role == UserRole.ADMIN:
        effective_seller_id = seller_id

    items = await InventoryService.list_seller_inventory(
        db=db,
        seller_id=effective_seller_id,
        low_stock_only=low_stock_only,
        skip=skip,
        limit=limit,
    )
    return [InventoryResponse.model_validate(item) for item in items]


@router.get("/{variant_id}", response_model=InventoryResponse, summary="Get variant inventory details")
async def get_inventory(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> InventoryResponse:
    """Retrieve full inventory details for a SKU. Enforces seller ownership or admin access."""
    await get_variant_and_check_ownership(db, variant_id, current_user)
    item = await InventoryService.get_by_variant_id(db, variant_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record for variant '{variant_id}' not found.",
        )
    return InventoryResponse.model_validate(item)


@router.patch("/{variant_id}", response_model=InventoryResponse, summary="Update variant stock level or threshold")
async def update_inventory(
    variant_id: uuid.UUID,
    payload: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> InventoryResponse:
    """Set absolute stock quantity or adjust low stock threshold. Enforces seller ownership."""
    await get_variant_and_check_ownership(db, variant_id, current_user)
    updated = await InventoryService.set_stock(
        db=db,
        variant_id=variant_id,
        quantity_on_hand=payload.quantity_on_hand,
        low_stock_threshold=payload.low_stock_threshold,
    )
    return InventoryResponse.model_validate(updated)


@router.post("/{variant_id}/adjust", response_model=InventoryResponse, summary="Adjust variant stock on hand")
async def adjust_inventory(
    variant_id: uuid.UUID,
    payload: InventoryAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> InventoryResponse:
    """Adjust stock on hand by an integer delta (+/-). Enforces seller ownership and non-negative stock."""
    await get_variant_and_check_ownership(db, variant_id, current_user)
    updated = await InventoryService.adjust_stock(
        db=db,
        variant_id=variant_id,
        adjustment=payload.adjustment,
        reason=payload.reason,
    )
    return InventoryResponse.model_validate(updated)


@router.get(
    "/{variant_id}/public",
    response_model=PublicVariantStockResponse,
    summary="Get public stock availability for variant",
)
async def get_public_stock(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicVariantStockResponse:
    """
    Public availability check for shoppers.
    Never exposes internal quantity numbers (quantity_on_hand, quantity_reserved).
    Returns only whether the item is in stock (quantity_available > 0).
    """
    stmt = (
        select(ProductVariant)
        .where(ProductVariant.id == variant_id)
        .options(
            selectinload(ProductVariant.product),
            selectinload(ProductVariant.inventory),
        )
    )
    res = await db.execute(stmt)
    variant = res.scalar_one_or_none()
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id '{variant_id}' not found.",
        )

    # Check if parent product is publicly visible
    product = variant.product
    if (
        not product
        or product.status != ProductStatus.ACTIVE
        or not product.is_active
        or not variant.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id '{variant_id}' not found.",
        )

    is_in_stock = variant.inventory.is_in_stock if variant.inventory else False
    return PublicVariantStockResponse(variant_id=variant.id, is_in_stock=is_in_stock)
