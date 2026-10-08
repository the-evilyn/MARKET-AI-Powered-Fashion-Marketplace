from decimal import Decimal
import math
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.seller.enums import StoreStatus
from app.modules.seller.models import Store
from app.modules.stores.schemas import (
    PublicStoreProductItem,
    PublicStoreProductsResponse,
    PublicStoreResponse,
)


class PublicStoreService:
    """Service layer for public store lookup and store-scoped catalog browsing."""

    @staticmethod
    async def get_public_store(db: AsyncSession, slug: str) -> PublicStoreResponse:
        """
        Retrieve public store details by slug.
        Only ACTIVE stores are visible. PENDING, SUSPENDED, and REJECTED return 404.
        Never exposes sensitive seller data (seller_id, user email, password_hash, etc.).
        """
        slug_clean = slug.strip().lower()
        stmt = select(Store).where(
            Store.slug == slug_clean,
            Store.status == StoreStatus.ACTIVE,
        )
        res = await db.execute(stmt)
        store = res.scalar_one_or_none()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{slug}' not found or currently unavailable.",
            )

        # Count active products
        count_stmt = select(func.count(Product.id)).where(
            Product.seller_id == store.seller_id,
            Product.status == ProductStatus.ACTIVE,
            Product.is_active.is_(True),
        )
        active_products_count = (await db.execute(count_stmt)).scalar() or 0

        return PublicStoreResponse(
            store_name=store.store_name,
            slug=store.slug,
            bio=store.bio,
            logo_url=store.logo_url,
            banner_url=store.banner_url,
            contact_email=store.contact_email,
            is_verified=store.is_verified,
            created_at=store.created_at,
            active_products_count=active_products_count,
        )

    @staticmethod
    async def get_public_store_products(
        db: AsyncSession,
        slug: str,
        category_id: Optional[uuid.UUID] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort_by: Optional[str] = "newest",
        page: int = 1,
        page_size: int = 20,
    ) -> PublicStoreProductsResponse:
        """
        Retrieve public active products belonging exclusively to the specified store.
        Filters: Store.status == ACTIVE, Product.status == ACTIVE, Product.is_active == True.
        Safe inventory mapping: only exposes boolean is_in_stock.
        """
        slug_clean = slug.strip().lower()
        store_stmt = select(Store).where(
            Store.slug == slug_clean,
            Store.status == StoreStatus.ACTIVE,
        )
        store_res = await db.execute(store_stmt)
        store = store_res.scalar_one_or_none()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{slug}' not found or currently unavailable.",
            )

        # Build base filter
        base_conditions = [
            Product.seller_id == store.seller_id,
            Product.status == ProductStatus.ACTIVE,
            Product.is_active.is_(True),
        ]
        if category_id is not None:
            base_conditions.append(Product.category_id == category_id)
        if min_price is not None:
            base_conditions.append(Product.base_price >= min_price)
        if max_price is not None:
            base_conditions.append(Product.base_price <= max_price)

        # Count total items
        total_stmt = select(func.count(Product.id)).where(*base_conditions)
        total = (await db.execute(total_stmt)).scalar() or 0

        # Query items with relations
        query = (
            select(Product)
            .options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.variants).selectinload(ProductVariant.inventory),
                selectinload(Product.media),
            )
            .where(*base_conditions)
        )

        # Sorting
        if sort_by == "price_asc":
            query = query.order_by(Product.base_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.base_price.desc())
        else:  # newest / default
            query = query.order_by(Product.created_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        products = (await db.execute(query)).scalars().all()

        items = []
        for p in products:
            # Determine is_in_stock: any active variant with inventory > 0
            is_in_stock = False
            active_variants = [v for v in p.variants if v.is_active]
            for v in active_variants:
                if v.inventory and v.inventory.quantity_available > 0:
                    is_in_stock = True
                    break

            # Find primary image
            primary_media = next((m for m in p.media if m.is_primary), p.media[0] if p.media else None)
            primary_image_url = primary_media.url if primary_media else None

            items.append(
                PublicStoreProductItem(
                    id=p.id,
                    name=p.name,
                    slug=p.slug,
                    base_price=p.base_price,
                    currency=p.currency,
                    brand_name=p.brand.name if p.brand else None,
                    category_name=p.category.name if p.category else None,
                    primary_image_url=primary_image_url,
                    is_in_stock=is_in_stock,
                    variants_count=len(active_variants),
                )
            )

        total_pages = math.ceil(total / page_size) if page_size > 0 else 0

        return PublicStoreProductsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
