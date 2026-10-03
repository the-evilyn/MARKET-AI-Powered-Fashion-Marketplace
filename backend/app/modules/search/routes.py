import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.search.schemas import (
    SearchFilterOptionsResponse,
    SearchProductsResponse,
    SearchQueryParams,
    SearchSort,
)
from app.modules.search.service import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/products",
    response_model=SearchProductsResponse,
    summary="Search and filter marketplace products",
)
async def search_products(
    q: Optional[str] = Query(default=None, description="Free-text search query"),
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter by category UUID"),
    brand_id: Optional[uuid.UUID] = Query(default=None, description="Filter by brand UUID"),
    min_price: Optional[Decimal] = Query(default=None, ge=Decimal("0.00"), description="Minimum price bound"),
    max_price: Optional[Decimal] = Query(default=None, ge=Decimal("0.00"), description="Maximum price bound"),
    size: Optional[str] = Query(default=None, max_length=50, description="Garment/shoe size filter"),
    color: Optional[str] = Query(default=None, max_length=50, description="Color filter"),
    in_stock: Optional[bool] = Query(default=None, description="Stock availability filter"),
    sort: Optional[SearchSort] = Query(default=None, description="Sorting order"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> SearchProductsResponse:
    """Discover active public marketplace listings with search keywords, facets, and pagination."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price.",
        )

    params = SearchQueryParams(
        q=q,
        category_id=category_id,
        brand_id=brand_id,
        min_price=min_price,
        max_price=max_price,
        size=size,
        color=color,
        in_stock=in_stock,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return await search_service.search_products(db=db, params=params)


@router.get(
    "/filters",
    response_model=SearchFilterOptionsResponse,
    summary="Get marketplace discovery filter options",
)
async def get_filter_options(
    db: AsyncSession = Depends(get_db),
) -> SearchFilterOptionsResponse:
    """Retrieve active categories, brands, sizes, colors, and price bounds for catalog discovery."""
    return await search_service.get_filter_options(db=db)
