import math
from decimal import Decimal
from typing import List, Optional, Protocol, Tuple

from sqlalchemy import (
    and_,
    case,
    distinct,
    exists,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import (
    Brand,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)
from app.modules.inventory.models import InventoryItem
from app.modules.search.schemas import (
    FilterBrandOption,
    FilterCategoryOption,
    SearchFilterOptionsResponse,
    SearchProductBrandItem,
    SearchProductCategoryItem,
    SearchProductItem,
    SearchProductMediaItem,
    SearchProductsResponse,
    SearchProductVariantItem,
    SearchQueryParams,
    SearchSort,
)


class SearchProvider(Protocol):
    """Abstract interface for marketplace product search and discovery providers."""

    async def search_products(
        self,
        db: AsyncSession,
        params: SearchQueryParams,
    ) -> SearchProductsResponse:
        ...

    async def get_filter_options(
        self,
        db: AsyncSession,
    ) -> SearchFilterOptionsResponse:
        ...


class PostgresSearchProvider:
    """PostgreSQL authoritative search and filtering provider."""

    async def search_products(
        self,
        db: AsyncSession,
        params: SearchQueryParams,
    ) -> SearchProductsResponse:
        base_conditions = [
            Product.status == ProductStatus.ACTIVE,
            Product.is_active == True,
        ]

        # 1. Category filter
        if params.category_id is not None:
            base_conditions.append(Product.category_id == params.category_id)

        # 2. Brand filter
        if params.brand_id is not None:
            base_conditions.append(Product.brand_id == params.brand_id)

        # 3. Price range filter
        price_conditions = []
        if params.min_price is not None:
            price_conditions.append(
                or_(
                    Product.base_price >= params.min_price,
                    exists(
                        select(1)
                        .select_from(ProductVariant)
                        .where(
                            ProductVariant.product_id == Product.id,
                            ProductVariant.is_active == True,
                            ProductVariant.price >= params.min_price,
                        )
                    ),
                )
            )
        if params.max_price is not None:
            price_conditions.append(
                or_(
                    Product.base_price <= params.max_price,
                    exists(
                        select(1)
                        .select_from(ProductVariant)
                        .where(
                            ProductVariant.product_id == Product.id,
                            ProductVariant.is_active == True,
                            ProductVariant.price <= params.max_price,
                        )
                    ),
                )
            )
        if price_conditions:
            base_conditions.extend(price_conditions)

        # 4. Variant attributes filter (size, color, in_stock)
        variant_filter_clauses = [
            ProductVariant.product_id == Product.id,
            ProductVariant.is_active == True,
        ]
        has_variant_filter = False

        if params.size:
            clean_size = params.size.strip().lower()
            variant_filter_clauses.append(func.lower(ProductVariant.size) == clean_size)
            has_variant_filter = True

        if params.color:
            clean_color = params.color.strip().lower()
            variant_filter_clauses.append(func.lower(ProductVariant.color) == clean_color)
            has_variant_filter = True

        if params.in_stock is True:
            variant_filter_clauses.append(
                exists(
                    select(1)
                    .select_from(InventoryItem)
                    .where(
                        InventoryItem.variant_id == ProductVariant.id,
                        (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved) > 0,
                    )
                )
            )
            has_variant_filter = True
        elif params.in_stock is False:
            variant_filter_clauses.append(
                or_(
                    ~exists(
                        select(1)
                        .select_from(InventoryItem)
                        .where(InventoryItem.variant_id == ProductVariant.id)
                    ),
                    exists(
                        select(1)
                        .select_from(InventoryItem)
                        .where(
                            InventoryItem.variant_id == ProductVariant.id,
                            (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved) <= 0,
                        )
                    ),
                )
            )
            has_variant_filter = True

        if has_variant_filter:
            base_conditions.append(
                exists(
                    select(1)
                    .select_from(ProductVariant)
                    .where(*variant_filter_clauses)
                )
            )

        # 5. Free-text search query (q)
        relevance_expr = None
        clean_q = params.q.strip() if params.q else ""
        if clean_q:
            clean_lower = clean_q.lower()
            search_pattern = f"%{clean_lower}%"
            starts_pattern = f"{clean_lower}%"

            q_conditions = [
                func.lower(Product.name).ilike(search_pattern),
                func.coalesce(func.lower(Product.description), "").ilike(search_pattern),
                func.lower(Product.slug).ilike(search_pattern),
                # Brand match
                exists(
                    select(1)
                    .select_from(Brand)
                    .where(
                        Brand.id == Product.brand_id,
                        Brand.is_active == True,
                        func.lower(Brand.name).ilike(search_pattern),
                    )
                ),
                # Category match
                exists(
                    select(1)
                    .select_from(Category)
                    .where(
                        Category.id == Product.category_id,
                        Category.is_active == True,
                        func.lower(Category.name).ilike(search_pattern),
                    )
                ),
                # Variant SKU, color, or size match
                exists(
                    select(1)
                    .select_from(ProductVariant)
                    .where(
                        ProductVariant.product_id == Product.id,
                        ProductVariant.is_active == True,
                        or_(
                            func.lower(ProductVariant.sku).ilike(search_pattern),
                            func.coalesce(func.lower(ProductVariant.color), "").ilike(search_pattern),
                            func.coalesce(func.lower(ProductVariant.size), "").ilike(search_pattern),
                        ),
                    )
                ),
            ]
            base_conditions.append(or_(*q_conditions))

            # Deterministic relevance ranking:
            # 1: Exact product name match
            # 2: Product name starts with query
            # 3: Product name contains query
            # 4: Description contains query
            # 5: Brand / Category / Variant match
            relevance_expr = case(
                (func.lower(Product.name) == clean_lower, 1),
                (func.lower(Product.name).ilike(starts_pattern), 2),
                (func.lower(Product.name).ilike(search_pattern), 3),
                (func.coalesce(func.lower(Product.description), "").ilike(search_pattern), 4),
                else_=5,
            )

        # Count total matching products
        count_stmt = select(func.count(Product.id)).where(*base_conditions)
        count_result = await db.execute(count_stmt)
        total: int = count_result.scalar_one() or 0

        # Construct items query
        stmt = (
            select(Product)
            .where(*base_conditions)
            .options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.media),
                selectinload(Product.variants).selectinload(ProductVariant.inventory),
            )
        )

        # Determine sort order
        effective_sort = params.sort
        if effective_sort is None:
            effective_sort = SearchSort.relevance if clean_q else SearchSort.newest

        if effective_sort == SearchSort.relevance:
            if relevance_expr is not None:
                stmt = stmt.order_by(relevance_expr.asc(), Product.created_at.desc(), Product.id.asc())
            else:
                stmt = stmt.order_by(Product.created_at.desc(), Product.id.asc())
        elif effective_sort == SearchSort.price_asc:
            stmt = stmt.order_by(Product.base_price.asc(), Product.id.asc())
        elif effective_sort == SearchSort.price_desc:
            stmt = stmt.order_by(Product.base_price.desc(), Product.id.asc())
        elif effective_sort == SearchSort.newest:
            stmt = stmt.order_by(Product.created_at.desc(), Product.id.asc())
        elif effective_sort == SearchSort.oldest:
            stmt = stmt.order_by(Product.created_at.asc(), Product.id.asc())
        elif effective_sort == SearchSort.name_asc:
            stmt = stmt.order_by(func.lower(Product.name).asc(), Product.id.asc())
        elif effective_sort == SearchSort.name_desc:
            stmt = stmt.order_by(func.lower(Product.name).desc(), Product.id.asc())
        else:
            stmt = stmt.order_by(Product.created_at.desc(), Product.id.asc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        result = await db.execute(stmt)
        products = list(result.scalars().all())

        # Transform to public search items
        items: List[SearchProductItem] = []
        for product in products:
            # Only active variants are exposed publicly
            active_variants = [v for v in product.variants if v.is_active]
            variant_items: List[SearchProductVariantItem] = []
            has_stock = False

            for v in active_variants:
                v_in_stock = v.is_in_stock
                if v_in_stock:
                    has_stock = True
                variant_items.append(
                    SearchProductVariantItem(
                        id=v.id,
                        product_id=v.product_id,
                        sku=v.sku,
                        color=v.color,
                        size=v.size,
                        price=v.price,
                        compare_at_price=v.compare_at_price,
                        is_active=v.is_active,
                        is_in_stock=v_in_stock,
                    )
                )

            media_items = [
                SearchProductMediaItem(
                    id=m.id,
                    url=m.url,
                    alt_text=m.alt_text,
                    sort_order=m.sort_order,
                    is_primary=m.is_primary,
                )
                for m in product.media
            ]

            brand_item = (
                SearchProductBrandItem(
                    id=product.brand.id,
                    name=product.brand.name,
                    slug=product.brand.slug,
                )
                if product.brand and product.brand.is_active
                else None
            )

            category_item = (
                SearchProductCategoryItem(
                    id=product.category.id,
                    name=product.category.name,
                    slug=product.category.slug,
                )
                if product.category and product.category.is_active
                else None
            )

            items.append(
                SearchProductItem(
                    id=product.id,
                    name=product.name,
                    slug=product.slug,
                    description=product.description,
                    base_price=product.base_price,
                    currency=product.currency,
                    status=product.status,
                    is_active=product.is_active,
                    brand=brand_item,
                    category=category_item,
                    variants=variant_items,
                    media=media_items,
                    is_in_stock=has_stock,
                )
            )

        total_pages = math.ceil(total / params.page_size) if total > 0 else 0
        has_next = params.page < total_pages
        has_previous = params.page > 1 and total > 0

        return SearchProductsResponse(
            items=items,
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )

    async def get_filter_options(
        self,
        db: AsyncSession,
    ) -> SearchFilterOptionsResponse:
        # 1. Categories having at least one active listing
        cat_stmt = (
            select(Category)
            .where(
                Category.is_active == True,
                exists(
                    select(1)
                    .select_from(Product)
                    .where(
                        Product.category_id == Category.id,
                        Product.status == ProductStatus.ACTIVE,
                        Product.is_active == True,
                    )
                ),
            )
            .order_by(Category.name.asc())
        )
        cat_res = await db.execute(cat_stmt)
        categories = [
            FilterCategoryOption(id=c.id, name=c.name, slug=c.slug)
            for c in cat_res.scalars().all()
        ]

        # 2. Brands having at least one active listing
        brand_stmt = (
            select(Brand)
            .where(
                Brand.is_active == True,
                exists(
                    select(1)
                    .select_from(Product)
                    .where(
                        Product.brand_id == Brand.id,
                        Product.status == ProductStatus.ACTIVE,
                        Product.is_active == True,
                    )
                ),
            )
            .order_by(Brand.name.asc())
        )
        brand_res = await db.execute(brand_stmt)
        brands = [
            FilterBrandOption(id=b.id, name=b.name, slug=b.slug)
            for b in brand_res.scalars().all()
        ]

        # 3. Distinct sizes from active variants of active products
        size_stmt = (
            select(ProductVariant.size)
            .distinct()
            .join(Product, Product.id == ProductVariant.product_id)
            .where(
                Product.status == ProductStatus.ACTIVE,
                Product.is_active == True,
                ProductVariant.is_active == True,
                ProductVariant.size.is_not(None),
                ProductVariant.size != "",
            )
            .order_by(ProductVariant.size.asc())
        )
        size_res = await db.execute(size_stmt)
        sizes = [s for s in size_res.scalars().all() if s]

        # 4. Distinct colors from active variants of active products
        color_stmt = (
            select(ProductVariant.color)
            .distinct()
            .join(Product, Product.id == ProductVariant.product_id)
            .where(
                Product.status == ProductStatus.ACTIVE,
                Product.is_active == True,
                ProductVariant.is_active == True,
                ProductVariant.color.is_not(None),
                ProductVariant.color != "",
            )
            .order_by(ProductVariant.color.asc())
        )
        color_res = await db.execute(color_stmt)
        colors = [c for c in color_res.scalars().all() if c]

        # 5. Price bounds across active listings and active variants
        prod_price_stmt = (
            select(
                func.min(Product.base_price).label("min_p"),
                func.max(Product.base_price).label("max_p"),
            ).where(
                Product.status == ProductStatus.ACTIVE,
                Product.is_active == True,
            )
        )
        prod_price_res = await db.execute(prod_price_stmt)
        prod_min, prod_max = prod_price_res.one_or_none() or (None, None)

        variant_price_stmt = (
            select(
                func.min(ProductVariant.price).label("min_v"),
                func.max(ProductVariant.price).label("max_v"),
            )
            .join(Product, Product.id == ProductVariant.product_id)
            .where(
                Product.status == ProductStatus.ACTIVE,
                Product.is_active == True,
                ProductVariant.is_active == True,
            )
        )
        var_price_res = await db.execute(variant_price_stmt)
        var_min, var_max = var_price_res.one_or_none() or (None, None)

        all_mins = [p for p in (prod_min, var_min) if p is not None]
        all_maxs = [p for p in (prod_max, var_max) if p is not None]

        min_price = min(all_mins) if all_mins else Decimal("0.00")
        max_price = max(all_maxs) if all_maxs else Decimal("0.00")

        return SearchFilterOptionsResponse(
            categories=categories,
            brands=brands,
            sizes=sizes,
            colors=colors,
            min_price=min_price,
            max_price=max_price,
        )
