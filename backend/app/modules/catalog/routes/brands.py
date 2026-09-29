import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.catalog.schemas import BrandCreate, BrandResponse, BrandUpdate
from app.modules.catalog.service import BrandService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("", response_model=List[BrandResponse], summary="List brands")
async def list_brands(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> List[BrandResponse]:
    """Retrieve brands with optional pagination and active status filtering."""
    brands = await BrandService.get_all(db, skip=skip, limit=limit, is_active=is_active)
    return [BrandResponse.model_validate(b) for b in brands]


@router.get("/{brand_id}", response_model=BrandResponse, summary="Get brand by ID")
async def get_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Retrieve details of a single brand."""
    brand = await BrandService.get_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id '{brand_id}' not found.",
        )
    return BrandResponse.model_validate(brand)


@router.post(
    "",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brand (Admin only)",
)
async def create_brand(
    payload: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> BrandResponse:
    """Create a new catalog brand. Requires ADMIN role."""
    brand = await BrandService.create(db, payload)
    return BrandResponse.model_validate(brand)


@router.patch("/{brand_id}", response_model=BrandResponse, summary="Update brand (Admin only)")
async def update_brand(
    brand_id: uuid.UUID,
    payload: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> BrandResponse:
    """Update brand metadata or status. Requires ADMIN role."""
    brand = await BrandService.get_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id '{brand_id}' not found.",
        )
    updated = await BrandService.update(db, brand, payload)
    return BrandResponse.model_validate(updated)


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brand (Admin only)",
)
async def delete_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> None:
    """Delete a brand entity. Requires ADMIN role."""
    brand = await BrandService.get_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id '{brand_id}' not found.",
        )
    await BrandService.delete(db, brand)
