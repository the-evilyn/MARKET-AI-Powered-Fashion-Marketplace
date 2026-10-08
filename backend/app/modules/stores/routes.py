from decimal import Decimal
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.stores.schemas import (
    PublicStoreProductsResponse,
    PublicStoreResponse,
)
from app.modules.stores.service import PublicStoreService

router = APIRouter(prefix="/stores", tags=["Public Stores"])


@router.get(
    "/{slug}",
    response_model=PublicStoreResponse,
    summary="Get public store profile by slug",
)
async def get_public_store(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> PublicStoreResponse:
    """
    Retrieve publicly visible storefront information.
    Does not require authentication. Returns 404 if the store does not exist or is not ACTIVE.
    """
    return await PublicStoreService.get_public_store(db, slug)


@router.get(
    "/{slug}/products",
    response_model=PublicStoreProductsResponse,
    summary="List public active products belonging to a store",
)
async def get_public_store_products(
    slug: str,
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter by category UUID"),
    min_price: Optional[Decimal] = Query(default=None, ge=Decimal("0.00"), description="Minimum base price"),
    max_price: Optional[Decimal] = Query(default=None, ge=Decimal("0.00"), description="Maximum base price"),
    sort_by: Optional[str] = Query(default="newest", description="Sorting criteria: newest, price_asc, price_desc"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page (max 50)"),
    db: AsyncSession = Depends(get_db),
) -> PublicStoreProductsResponse:
    """
    Retrieve active catalog items belonging to the requested store.
    Does not require authentication. Never exposes draft/archived products or internal inventory details.
    """
    return await PublicStoreService.get_public_store_products(
        db=db,
        slug=slug,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
