import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.enums import ProductStatus, MediaType
from app.modules.catalog.models import (
    Brand,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)
from app.modules.inventory.models import InventoryItem
from app.modules.catalog.schemas import (
    BrandCreate,
    BrandUpdate,
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductMediaCreate,
    ProductMediaUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
    slugify,
)


class BrandService:
    """Service layer managing brand entities."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
    ) -> List[Brand]:
        stmt = select(Brand)
        if is_active is not None:
            stmt = stmt.where(Brand.is_active == is_active)
        stmt = stmt.order_by(Brand.name.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, brand_id: uuid.UUID) -> Optional[Brand]:
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Brand]:
        stmt = select(Brand).where(Brand.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, payload: BrandCreate) -> Brand:
        raw_slug = payload.slug if payload.slug else payload.name
        normalized_slug = slugify(raw_slug)
        if not normalized_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand name must generate a valid slug.",
            )

        existing = await BrandService.get_by_slug(db, normalized_slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A brand with slug '{normalized_slug}' already exists.",
            )

        brand = Brand(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            slug=normalized_slug,
            description=payload.description.strip() if payload.description else None,
            logo_url=payload.logo_url.strip() if payload.logo_url else None,
            is_active=payload.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return brand

    @staticmethod
    async def update(db: AsyncSession, brand: Brand, payload: BrandUpdate) -> Brand:
        if payload.name is not None:
            brand.name = payload.name.strip()
        if payload.slug is not None or (payload.name is not None and payload.slug is None):
            raw_slug = payload.slug if payload.slug is not None else brand.name
            normalized_slug = slugify(raw_slug)
            if normalized_slug and normalized_slug != brand.slug:
                existing = await BrandService.get_by_slug(db, normalized_slug)
                if existing and existing.id != brand.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A brand with slug '{normalized_slug}' already exists.",
                    )
                brand.slug = normalized_slug
        if payload.description is not None:
            brand.description = payload.description.strip() if payload.description else None
        if payload.logo_url is not None:
            brand.logo_url = payload.logo_url.strip() if payload.logo_url else None
        if payload.is_active is not None:
            brand.is_active = payload.is_active

        brand.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(brand)
        return brand

    @staticmethod
    async def delete(db: AsyncSession, brand: Brand) -> None:
        await db.delete(brand)
        await db.commit()


class CategoryService:
    """Service layer managing hierarchical categories."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        parent_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[Category]:
        stmt = select(Category)
        if parent_id is not None:
            stmt = stmt.where(Category.parent_id == parent_id)
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
        stmt = stmt.order_by(Category.name.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(Category.id == category_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, payload: CategoryCreate) -> Category:
        raw_slug = payload.slug if payload.slug else payload.name
        normalized_slug = slugify(raw_slug)
        if not normalized_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name must generate a valid slug.",
            )

        existing = await CategoryService.get_by_slug(db, normalized_slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A category with slug '{normalized_slug}' already exists.",
            )

        if payload.parent_id is not None:
            parent = await CategoryService.get_by_id(db, payload.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with id '{payload.parent_id}' does not exist.",
                )

        category = Category(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            slug=normalized_slug,
            description=payload.description.strip() if payload.description else None,
            parent_id=payload.parent_id,
            is_active=payload.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(db: AsyncSession, category: Category, payload: CategoryUpdate) -> Category:
        if payload.parent_id is not None:
            if payload.parent_id == category.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A category cannot be its own parent.",
                )
            parent = await CategoryService.get_by_id(db, payload.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with id '{payload.parent_id}' does not exist.",
                )

            # Circular hierarchy prevention: traverse parent chain upwards
            curr_ancestor_id: Optional[uuid.UUID] = parent.parent_id
            visited = {category.id, payload.parent_id}
            while curr_ancestor_id is not None:
                if curr_ancestor_id == category.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Circular category hierarchy is not allowed.",
                    )
                if curr_ancestor_id in visited:
                    break
                visited.add(curr_ancestor_id)
                ancestor = await CategoryService.get_by_id(db, curr_ancestor_id)
                curr_ancestor_id = ancestor.parent_id if ancestor else None

            category.parent_id = payload.parent_id

        if payload.name is not None:
            category.name = payload.name.strip()
        if payload.slug is not None or (payload.name is not None and payload.slug is None):
            raw_slug = payload.slug if payload.slug is not None else category.name
            normalized_slug = slugify(raw_slug)
            if normalized_slug and normalized_slug != category.slug:
                existing = await CategoryService.get_by_slug(db, normalized_slug)
                if existing and existing.id != category.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A category with slug '{normalized_slug}' already exists.",
                    )
                category.slug = normalized_slug
        if payload.description is not None:
            category.description = payload.description.strip() if payload.description else None
        if payload.is_active is not None:
            category.is_active = payload.is_active

        category.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category: Category) -> None:
        await db.delete(category)
        await db.commit()


class ProductService:
    """Service layer managing products and seller ownership."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        seller_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        status_filter: Optional[ProductStatus] = None,
        is_active: Optional[bool] = None,
    ) -> List[Product]:
        stmt = select(Product)
        if seller_id is not None:
            stmt = stmt.where(Product.seller_id == seller_id)
        if brand_id is not None:
            stmt = stmt.where(Product.brand_id == brand_id)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if status_filter is not None:
            stmt = stmt.where(Product.status == status_filter)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        stmt = stmt.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        product_id: uuid.UUID,
        load_details: bool = False,
    ) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id)
        if load_details:
            stmt = stmt.options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.media),
            )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Product]:
        stmt = select(Product).where(Product.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        seller_id: uuid.UUID,
        payload: ProductCreate,
    ) -> Product:
        raw_slug = payload.slug if payload.slug else payload.name
        normalized_slug = slugify(raw_slug)
        if not normalized_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name must generate a valid slug.",
            )

        existing = await ProductService.get_by_slug(db, normalized_slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with slug '{normalized_slug}' already exists.",
            )

        if payload.brand_id is not None:
            brand = await BrandService.get_by_id(db, payload.brand_id)
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brand with id '{payload.brand_id}' does not exist.",
                )

        if payload.category_id is not None:
            category = await CategoryService.get_by_id(db, payload.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with id '{payload.category_id}' does not exist.",
                )

        product = Product(
            id=uuid.uuid4(),
            seller_id=seller_id,
            brand_id=payload.brand_id,
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=normalized_slug,
            description=payload.description.strip() if payload.description else None,
            status=payload.status,
            base_price=payload.base_price,
            currency=payload.currency.upper(),
            is_active=payload.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def update(
        db: AsyncSession,
        product: Product,
        payload: ProductUpdate,
    ) -> Product:
        if payload.name is not None:
            product.name = payload.name.strip()
        if payload.slug is not None or (payload.name is not None and payload.slug is None):
            raw_slug = payload.slug if payload.slug is not None else product.name
            normalized_slug = slugify(raw_slug)
            if normalized_slug and normalized_slug != product.slug:
                existing = await ProductService.get_by_slug(db, normalized_slug)
                if existing and existing.id != product.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A product with slug '{normalized_slug}' already exists.",
                    )
                product.slug = normalized_slug
        if payload.description is not None:
            product.description = payload.description.strip() if payload.description else None
        if payload.brand_id is not None:
            brand = await BrandService.get_by_id(db, payload.brand_id)
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brand with id '{payload.brand_id}' does not exist.",
                )
            product.brand_id = payload.brand_id
        if payload.category_id is not None:
            category = await CategoryService.get_by_id(db, payload.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with id '{payload.category_id}' does not exist.",
                )
            product.category_id = payload.category_id
        if payload.status is not None:
            product.status = payload.status
        if payload.base_price is not None:
            product.base_price = payload.base_price
        if payload.currency is not None:
            product.currency = payload.currency.upper()
        if payload.is_active is not None:
            product.is_active = payload.is_active

        product.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def delete(db: AsyncSession, product: Product) -> None:
        await db.delete(product)
        await db.commit()


class VariantService:
    """Service layer managing product SKU variants."""

    @staticmethod
    async def get_all_by_product(
        db: AsyncSession,
        product_id: uuid.UUID,
    ) -> List[ProductVariant]:
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        variant_id: uuid.UUID,
    ) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_sku(
        db: AsyncSession,
        sku: str,
    ) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).where(ProductVariant.sku == sku.strip())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        product_id: uuid.UUID,
        payload: ProductVariantCreate,
    ) -> ProductVariant:
        clean_sku = payload.sku.strip()
        existing = await VariantService.get_by_sku(db, clean_sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A variant with SKU '{clean_sku}' already exists.",
            )

        variant = ProductVariant(
            id=uuid.uuid4(),
            product_id=product_id,
            sku=clean_sku,
            color=payload.color.strip() if payload.color else None,
            size=payload.size.strip() if payload.size else None,
            price=payload.price,
            compare_at_price=payload.compare_at_price,
            is_active=payload.is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(variant)
        inventory = InventoryItem(
            id=uuid.uuid4(),
            variant_id=variant.id,
            quantity_on_hand=0,
            quantity_reserved=0,
            low_stock_threshold=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(inventory)
        await db.commit()
        await db.refresh(variant)
        return variant

    @staticmethod
    async def update(
        db: AsyncSession,
        variant: ProductVariant,
        payload: ProductVariantUpdate,
    ) -> ProductVariant:
        if payload.sku is not None:
            clean_sku = payload.sku.strip()
            if clean_sku != variant.sku:
                existing = await VariantService.get_by_sku(db, clean_sku)
                if existing and existing.id != variant.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A variant with SKU '{clean_sku}' already exists.",
                    )
                variant.sku = clean_sku

        effective_price = payload.price if payload.price is not None else variant.price
        effective_compare = (
            payload.compare_at_price
            if payload.compare_at_price is not None
            else variant.compare_at_price
        )
        if effective_compare is not None and effective_compare < effective_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="compare_at_price must be greater than or equal to price.",
            )

        if payload.price is not None:
            variant.price = payload.price
        if payload.compare_at_price is not None:
            variant.compare_at_price = payload.compare_at_price
        if payload.color is not None:
            variant.color = payload.color.strip() if payload.color else None
        if payload.size is not None:
            variant.size = payload.size.strip() if payload.size else None
        if payload.is_active is not None:
            variant.is_active = payload.is_active

        variant.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(variant)
        return variant

    @staticmethod
    async def delete(db: AsyncSession, variant: ProductVariant) -> None:
        await db.delete(variant)
        await db.commit()


class MediaService:
    """Service layer managing product media assets."""

    @staticmethod
    async def get_all_by_product(
        db: AsyncSession,
        product_id: uuid.UUID,
    ) -> List[ProductMedia]:
        stmt = (
            select(ProductMedia)
            .where(ProductMedia.product_id == product_id)
            .order_by(ProductMedia.sort_order.asc(), ProductMedia.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        media_id: uuid.UUID,
    ) -> Optional[ProductMedia]:
        stmt = select(ProductMedia).where(ProductMedia.id == media_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        product_id: uuid.UUID,
        payload: ProductMediaCreate,
    ) -> ProductMedia:
        media = ProductMedia(
            id=uuid.uuid4(),
            product_id=product_id,
            media_type=payload.media_type,
            url=payload.url.strip(),
            object_key=payload.object_key.strip() if payload.object_key else None,
            alt_text=payload.alt_text.strip() if payload.alt_text else None,
            sort_order=payload.sort_order,
            is_primary=payload.is_primary,
            file_size=payload.file_size,
            mime_type=payload.mime_type,
            original_filename=payload.original_filename,
            created_at=datetime.now(timezone.utc),
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)
        return media

    @staticmethod
    async def upload_and_create(
        db: AsyncSession,
        product_id: uuid.UUID,
        file_content: bytes,
        filename: str,
        content_type: str,
        alt_text: Optional[str] = None,
        sort_order: int = 0,
        is_primary: bool = False,
    ) -> ProductMedia:
        from app.core.storage import StorageService, validate_image_file

        ext = validate_image_file(file_content, filename, content_type)
        object_key = f"products/{product_id}/{uuid.uuid4().hex}{ext}"

        url = StorageService.upload_file(
            data=file_content,
            object_key=object_key,
            content_type=content_type,
        )

        media = ProductMedia(
            id=uuid.uuid4(),
            product_id=product_id,
            media_type=MediaType.IMAGE,
            url=url,
            object_key=object_key,
            alt_text=alt_text.strip() if alt_text else None,
            sort_order=sort_order,
            is_primary=is_primary,
            file_size=len(file_content),
            mime_type=content_type,
            original_filename=filename,
            created_at=datetime.now(timezone.utc),
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)
        return media

    @staticmethod
    async def update(
        db: AsyncSession,
        media: ProductMedia,
        payload: ProductMediaUpdate,
    ) -> ProductMedia:
        if payload.media_type is not None:
            media.media_type = payload.media_type
        if payload.url is not None:
            media.url = payload.url.strip()
        if payload.object_key is not None:
            media.object_key = payload.object_key.strip() if payload.object_key else None
        if payload.alt_text is not None:
            media.alt_text = payload.alt_text.strip() if payload.alt_text else None
        if payload.sort_order is not None:
            media.sort_order = payload.sort_order
        if payload.is_primary is not None:
            media.is_primary = payload.is_primary
        if payload.file_size is not None:
            media.file_size = payload.file_size
        if payload.mime_type is not None:
            media.mime_type = payload.mime_type
        if payload.original_filename is not None:
            media.original_filename = payload.original_filename

        await db.commit()
        await db.refresh(media)
        return media

    @staticmethod
    async def delete(db: AsyncSession, media: ProductMedia) -> None:
        if media.object_key:
            from app.core.storage import StorageService
            StorageService.delete_file(media.object_key)
        await db.delete(media)
        await db.commit()
