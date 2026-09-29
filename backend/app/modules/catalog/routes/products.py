import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_roles
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product
from app.modules.catalog.schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductMediaCreate,
    ProductMediaResponse,
    ProductMediaUpdate,
    ProductResponse,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
)
from app.modules.catalog.service import (
    MediaService,
    ProductService,
    VariantService,
)
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["Products"])


def check_product_ownership(product: Product, current_user: User) -> None:
    """Enforce that only the seller owning the product or an ADMIN can modify it."""
    if current_user.role != UserRole.ADMIN and product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this product.",
        )


def check_product_read_access(product: Product, current_user: Optional[User]) -> None:
    """Ensure non-ACTIVE or inactive products are only readable by owner seller or ADMIN."""
    is_publicly_visible = (product.status == ProductStatus.ACTIVE and product.is_active is True)
    if not is_publicly_visible:
        is_owner = (current_user is not None and current_user.id == product.seller_id)
        is_admin = (current_user is not None and current_user.role == UserRole.ADMIN)
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product.id}' not found.",
            )



# ==============================================================================
# Product Endpoints
# ==============================================================================

@router.get("", response_model=List[ProductResponse], summary="List products")
async def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    seller_id: Optional[uuid.UUID] = Query(default=None),
    brand_id: Optional[uuid.UUID] = Query(default=None),
    category_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[ProductStatus] = Query(default=None, alias="status"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> List[ProductResponse]:
    """Retrieve catalog products. Public access is restricted to ACTIVE and is_active=true."""
    if current_user and current_user.role == UserRole.ADMIN:
        effective_status = status_filter
        effective_is_active = is_active
    elif current_user and current_user.role == UserRole.SELLER and seller_id == current_user.id:
        effective_status = status_filter
        effective_is_active = is_active
    else:
        effective_status = ProductStatus.ACTIVE
        effective_is_active = True

    products = await ProductService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        seller_id=seller_id,
        brand_id=brand_id,
        category_id=category_id,
        status_filter=effective_status,
        is_active=effective_is_active,
    )
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductDetailResponse, summary="Get product details")
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ProductDetailResponse:
    """Retrieve full product details including variants, media, brand, and category."""
    product = await ProductService.get_by_id(db, product_id, load_details=True)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_read_access(product, current_user)
    return ProductDetailResponse.model_validate(product)



@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product (Seller or Admin)",
)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductResponse:
    """Create a new product listing. Automatically assigns ownership to authenticated seller."""
    product = await ProductService.create(db, seller_id=current_user.id, payload=payload)
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse, summary="Update product")
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductResponse:
    """Update product details. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)
    updated = await ProductService.update(db, product, payload)
    return ProductResponse.model_validate(updated)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete a product. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)
    await ProductService.delete(db, product)


# ==============================================================================
# Product Variant Endpoints
# ==============================================================================

@router.get(
    "/{product_id}/variants",
    response_model=List[ProductVariantResponse],
    summary="List product variants",
)
async def list_variants(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> List[ProductVariantResponse]:
    """Retrieve all purchasable SKU variants for a product."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_read_access(product, current_user)
    variants = await VariantService.get_all_by_product(db, product_id)
    return [ProductVariantResponse.model_validate(v) for v in variants]



@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product variant",
)
async def create_variant(
    product_id: uuid.UUID,
    payload: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductVariantResponse:
    """Add a new SKU variant to a product. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)
    variant = await VariantService.create(db, product_id=product_id, payload=payload)
    return ProductVariantResponse.model_validate(variant)


@router.patch(
    "/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Update product variant",
)
async def update_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductVariantResponse:
    """Update variant details. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)

    variant = await VariantService.get_by_id(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id '{variant_id}' not found for this product.",
        )

    updated = await VariantService.update(db, variant, payload)
    return ProductVariantResponse.model_validate(updated)


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product variant",
)
async def delete_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete a variant SKU. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)

    variant = await VariantService.get_by_id(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id '{variant_id}' not found for this product.",
        )

    await VariantService.delete(db, variant)


# ==============================================================================
# Product Media Endpoints
# ==============================================================================

@router.get(
    "/{product_id}/media",
    response_model=List[ProductMediaResponse],
    summary="List product media assets",
)
async def list_media(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> List[ProductMediaResponse]:
    """Retrieve all media assets for a product ordered by sequence."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_read_access(product, current_user)
    media_items = await MediaService.get_all_by_product(db, product_id)
    return [ProductMediaResponse.model_validate(m) for m in media_items]



@router.post(
    "/{product_id}/media",
    response_model=ProductMediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add product media asset",
)
async def create_media(
    product_id: uuid.UUID,
    payload: ProductMediaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductMediaResponse:
    """Add media asset metadata to a product. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)
    media = await MediaService.create(db, product_id=product_id, payload=payload)
    return ProductMediaResponse.model_validate(media)


@router.patch(
    "/{product_id}/media/{media_id}",
    response_model=ProductMediaResponse,
    summary="Update product media asset",
)
async def update_media(
    product_id: uuid.UUID,
    media_id: uuid.UUID,
    payload: ProductMediaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> ProductMediaResponse:
    """Update media asset metadata. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)

    media = await MediaService.get_by_id(db, media_id)
    if not media or media.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media with id '{media_id}' not found for this product.",
        )

    updated = await MediaService.update(db, media, payload)
    return ProductMediaResponse.model_validate(updated)


@router.delete(
    "/{product_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product media asset",
)
async def delete_media(
    product_id: uuid.UUID,
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SELLER, UserRole.ADMIN)),
) -> None:
    """Delete a media asset. Enforces seller ownership."""
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    check_product_ownership(product, current_user)

    media = await MediaService.get_by_id(db, media_id)
    if not media or media.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media with id '{media_id}' not found for this product.",
        )

    await MediaService.delete(db, media)
