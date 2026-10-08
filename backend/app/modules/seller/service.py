import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.storage import StorageService, validate_image_file
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.catalog.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
)
from app.modules.catalog.service import ProductService, VariantService
from app.modules.inventory.models import InventoryItem
from app.modules.inventory.service import InventoryService
from app.modules.orders.enums import OrderStatus
from app.modules.orders.models import Order, OrderItem, SubOrder
from app.modules.seller.enums import StoreStatus
from app.modules.seller.models import Store
from app.modules.seller.schemas import (
    SellerDashboardResponse,
    SellerInventoryItemResponse,
    SellerOrderItemResponse,
    SellerOrderResponse,
    SellerProfileResponse,
    SellerProfileUpdate,
    StoreMediaUploadResponse,
)
from app.modules.users.models import User

RESERVED_SLUGS = {
    "admin",
    "api",
    "auth",
    "store",
    "stores",
    "seller",
    "sellers",
    "products",
    "cart",
    "checkout",
    "orders",
    "payments",
    "settings",
    "dashboard",
    "terms",
    "privacy",
    "help",
    "support",
    "about",
    "search",
}

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(text: str) -> str:
    """Normalize text into a clean URL-friendly slug."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    if len(text) > 100:
        text = text[:100].rstrip("-")
    if len(text) < 3:
        text = f"store-{text}" if text else "store"
    return text


def is_valid_slug(slug: str) -> bool:
    """Validate slug format, length and reserved namespace."""
    if not (3 <= len(slug) <= 120):
        return False
    if not SLUG_REGEX.match(slug):
        return False
    if slug in RESERVED_SLUGS:
        return False
    return True


async def generate_unique_slug(
    db: AsyncSession,
    base_text: str,
    exclude_store_id: Optional[uuid.UUID] = None,
) -> str:
    """Generate a collision-free deterministic slug (e.g. maison-paris, maison-paris-2, ...)."""
    base_slug = normalize_slug(base_text)
    candidate = base_slug
    counter = 1

    while True:
        if candidate not in RESERVED_SLUGS:
            stmt = select(Store.id).where(Store.slug == candidate)
            if exclude_store_id:
                stmt = stmt.where(Store.id != exclude_store_id)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                return candidate

        counter += 1
        candidate = f"{base_slug}-{counter}"


class SellerService:
    """Service layer managing seller operations, dashboard KPIs, scoped catalog, inventory, orders, and store profile."""

    # ==========================================================================
    # Dashboard KPIs
    # ==========================================================================

    @staticmethod
    async def get_dashboard_kpis(
        db: AsyncSession,
        seller_id: Optional[uuid.UUID] = None,
    ) -> SellerDashboardResponse:
        """
        Derive dashboard KPIs directly from existing data.
        For SELLER, metrics are strictly isolated to items/products owned by that seller.
        For ADMIN (when seller_id is None), marketplace-wide metrics are returned.
        Sales metrics only count successfully CONFIRMED orders. Decimal arithmetic is strictly enforced.
        """
        if seller_id is not None:
            # 1. Total & Active Products
            total_prod_stmt = select(func.count(Product.id)).where(Product.seller_id == seller_id)
            total_products = (await db.execute(total_prod_stmt)).scalar() or 0

            active_prod_stmt = select(func.count(Product.id)).where(
                Product.seller_id == seller_id,
                Product.status == ProductStatus.ACTIVE,
                Product.is_active.is_(True),
            )
            active_products = (await db.execute(active_prod_stmt)).scalar() or 0

            # 2. Total Variants
            total_var_stmt = (
                select(func.count(ProductVariant.id))
                .join(Product, ProductVariant.product_id == Product.id)
                .where(Product.seller_id == seller_id)
            )
            total_variants = (await db.execute(total_var_stmt)).scalar() or 0

            # 3. Low Stock & Out of Stock Variants
            low_stock_stmt = (
                select(func.count(InventoryItem.id))
                .join(ProductVariant, InventoryItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(
                    Product.seller_id == seller_id,
                    (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved)
                    <= InventoryItem.low_stock_threshold,
                )
            )
            low_stock_variants = (await db.execute(low_stock_stmt)).scalar() or 0

            out_of_stock_stmt = (
                select(func.count(InventoryItem.id))
                .join(ProductVariant, InventoryItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(
                    Product.seller_id == seller_id,
                    (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved) <= 0,
                )
            )
            out_of_stock_variants = (await db.execute(out_of_stock_stmt)).scalar() or 0

            # 4. Orders containing this seller's products
            base_orders_query = (
                select(Order.id)
                .distinct()
                .join(OrderItem, Order.id == OrderItem.order_id)
                .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(Product.seller_id == seller_id)
            )

            total_orders_stmt = select(func.count()).select_from(base_orders_query.subquery())
            total_orders = (await db.execute(total_orders_stmt)).scalar() or 0

            pending_orders_query = base_orders_query.where(Order.status == OrderStatus.PENDING_PAYMENT)
            pending_orders_stmt = select(func.count()).select_from(pending_orders_query.subquery())
            pending_orders = (await db.execute(pending_orders_stmt)).scalar() or 0

            confirmed_orders_query = base_orders_query.where(Order.status == OrderStatus.CONFIRMED)
            confirmed_orders_stmt = select(func.count()).select_from(confirmed_orders_query.subquery())
            confirmed_orders = (await db.execute(confirmed_orders_stmt)).scalar() or 0

            cancelled_orders_query = base_orders_query.where(Order.status == OrderStatus.CANCELLED)
            cancelled_orders_stmt = select(func.count()).select_from(cancelled_orders_query.subquery())
            cancelled_orders = (await db.execute(cancelled_orders_stmt)).scalar() or 0

            # 5. Sales & Items Sold (Strictly CONFIRMED orders)
            sales_stmt = (
                select(func.coalesce(func.sum(OrderItem.line_total), Decimal("0.00")))
                .join(Order, OrderItem.order_id == Order.id)
                .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(
                    Product.seller_id == seller_id,
                    Order.status == OrderStatus.CONFIRMED,
                )
            )
            total_sales = (await db.execute(sales_stmt)).scalar() or Decimal("0.00")

            items_sold_stmt = (
                select(func.coalesce(func.sum(OrderItem.quantity), 0))
                .join(Order, OrderItem.order_id == Order.id)
                .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(
                    Product.seller_id == seller_id,
                    Order.status == OrderStatus.CONFIRMED,
                )
            )
            total_items_sold = (await db.execute(items_sold_stmt)).scalar() or 0

        else:
            # ADMIN GLOBAL METRICS
            total_products = (await db.execute(select(func.count(Product.id)))).scalar() or 0
            active_products = (
                await db.execute(
                    select(func.count(Product.id)).where(
                        Product.status == ProductStatus.ACTIVE,
                        Product.is_active.is_(True),
                    )
                )
            ).scalar() or 0
            total_variants = (await db.execute(select(func.count(ProductVariant.id)))).scalar() or 0

            low_stock_stmt = select(func.count(InventoryItem.id)).where(
                (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved)
                <= InventoryItem.low_stock_threshold
            )
            low_stock_variants = (await db.execute(low_stock_stmt)).scalar() or 0

            out_of_stock_stmt = select(func.count(InventoryItem.id)).where(
                (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved) <= 0
            )
            out_of_stock_variants = (await db.execute(out_of_stock_stmt)).scalar() or 0

            total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
            pending_orders = (
                await db.execute(
                    select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING_PAYMENT)
                )
            ).scalar() or 0
            confirmed_orders = (
                await db.execute(
                    select(func.count(Order.id)).where(Order.status == OrderStatus.CONFIRMED)
                )
            ).scalar() or 0
            cancelled_orders = (
                await db.execute(
                    select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)
                )
            ).scalar() or 0

            sales_stmt = select(func.coalesce(func.sum(Order.total), Decimal("0.00"))).where(
                Order.status == OrderStatus.CONFIRMED
            )
            total_sales = (await db.execute(sales_stmt)).scalar() or Decimal("0.00")

            items_sold_stmt = (
                select(func.coalesce(func.sum(OrderItem.quantity), 0))
                .join(Order, OrderItem.order_id == Order.id)
                .where(Order.status == OrderStatus.CONFIRMED)
            )
            total_items_sold = (await db.execute(items_sold_stmt)).scalar() or 0

        return SellerDashboardResponse(
            total_products=total_products,
            active_products=active_products,
            total_variants=total_variants,
            low_stock_variants=low_stock_variants,
            out_of_stock_variants=out_of_stock_variants,
            total_orders=total_orders,
            pending_orders=pending_orders,
            confirmed_orders=confirmed_orders,
            cancelled_orders=cancelled_orders,
            total_sales=Decimal(str(total_sales)),
            total_items_sold=total_items_sold,
        )

    # ==========================================================================
    # Product Management
    # ==========================================================================

    @staticmethod
    async def list_products(
        db: AsyncSession,
        seller_id: Optional[uuid.UUID] = None,
        status_filter: Optional[ProductStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:
        """List products owned by the seller (or all for admin), with optional status filters."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.media),
            )
            .order_by(Product.created_at.desc())
        )
        if seller_id is not None:
            stmt = stmt.where(Product.seller_id == seller_id)
        if status_filter is not None:
            stmt = stmt.where(Product.status == status_filter)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_product_by_id(
        db: AsyncSession,
        product_id: uuid.UUID,
        seller_id: Optional[uuid.UUID] = None,
    ) -> Product:
        """Fetch product by ID and enforce seller ownership."""
        product = await ProductService.get_by_id(db, product_id, load_details=True)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found.",
            )
        if seller_id is not None and product.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage this product.",
            )
        return product

    @staticmethod
    async def create_product(
        db: AsyncSession,
        seller_id: uuid.UUID,
        payload: ProductCreate,
    ) -> Product:
        """Create product strictly assigned to authenticated seller."""
        return await ProductService.create(db, seller_id=seller_id, payload=payload)

    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        payload: ProductUpdate,
    ) -> Product:
        """Update product ensuring seller ownership is preserved."""
        product = await SellerService.get_product_by_id(db, product_id, seller_id)
        return await ProductService.update(db, product, payload)

    @staticmethod
    async def delete_product(
        db: AsyncSession,
        product_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
    ) -> None:
        """
        Delete or safe-archive product.
        If product has existing orders, safe-archive (ARCHIVED + is_active=False)
        to prevent breaking historical snapshots and order visibility.
        If product has no orders, hard-delete.
        """
        product = await SellerService.get_product_by_id(db, product_id, seller_id)

        # Check if any variant has been ordered
        order_check = (
            select(OrderItem.id)
            .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
            .where(ProductVariant.product_id == product.id)
            .limit(1)
        )
        has_orders = (await db.execute(order_check)).first() is not None

        if has_orders:
            # Safe archive
            product.status = ProductStatus.ARCHIVED
            product.is_active = False
            product.updated_at = datetime.now(timezone.utc)
            for v in product.variants:
                v.is_active = False
                v.updated_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            await ProductService.delete(db, product)

    # ==========================================================================
    # Variant Management
    # ==========================================================================

    @staticmethod
    async def list_variants(
        db: AsyncSession,
        product_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
    ) -> List[ProductVariant]:
        """List SKU variants for a product owned by seller."""
        await SellerService.get_product_by_id(db, product_id, seller_id)
        return await VariantService.get_all_by_product(db, product_id)

    @staticmethod
    async def create_variant(
        db: AsyncSession,
        product_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        payload: ProductVariantCreate,
    ) -> ProductVariant:
        """Create SKU variant for a product owned by seller."""
        await SellerService.get_product_by_id(db, product_id, seller_id)
        return await VariantService.create(db, product_id=product_id, payload=payload)

    @staticmethod
    async def get_variant_by_id(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        product_id: Optional[uuid.UUID] = None,
    ) -> tuple[ProductVariant, Product]:
        """Fetch variant and enforce product and seller ownership."""
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
        if product_id is not None and variant.product_id != product_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant '{variant_id}' does not belong to product '{product_id}'.",
            )
        product = variant.product
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent product not found.",
            )
        if seller_id is not None and product.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage this variant.",
            )
        return variant, product

    @staticmethod
    async def update_variant(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        payload: ProductVariantUpdate,
        product_id: Optional[uuid.UUID] = None,
    ) -> ProductVariant:
        """Update SKU variant with ownership check."""
        variant, _ = await SellerService.get_variant_by_id(db, variant_id, seller_id, product_id)
        return await VariantService.update(db, variant, payload)

    @staticmethod
    async def delete_variant(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        product_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Delete or deactivate variant.
        If variant has order items, deactivate it (is_active=False) to preserve snapshots.
        Otherwise hard-delete.
        """
        variant, _ = await SellerService.get_variant_by_id(db, variant_id, seller_id, product_id)
        order_check = select(OrderItem.id).where(OrderItem.variant_id == variant.id).limit(1)
        has_orders = (await db.execute(order_check)).first() is not None

        if has_orders:
            variant.is_active = False
            variant.updated_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            await VariantService.delete(db, variant)

    # ==========================================================================
    # Inventory Management
    # ==========================================================================

    @staticmethod
    async def list_inventory(
        db: AsyncSession,
        seller_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SellerInventoryItemResponse]:
        """List inventory records for the seller, enriched with variant and product info."""
        stmt = (
            select(InventoryItem)
            .join(ProductVariant, InventoryItem.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .options(
                selectinload(InventoryItem.variant).selectinload(ProductVariant.product),
            )
        )
        if seller_id is not None:
            stmt = stmt.where(Product.seller_id == seller_id)
        if low_stock_only:
            stmt = stmt.where(
                (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved)
                <= InventoryItem.low_stock_threshold
            )

        stmt = stmt.order_by(InventoryItem.updated_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        items = list(res.scalars().all())

        return [
            SellerInventoryItemResponse(
                id=item.id,
                variant_id=item.variant_id,
                product_id=item.variant.product_id,
                product_name=item.variant.product.name,
                sku=item.variant.sku,
                color=item.variant.color,
                size=item.variant.size,
                price=item.variant.price,
                compare_at_price=item.variant.compare_at_price,
                quantity_on_hand=item.quantity_on_hand,
                quantity_reserved=item.quantity_reserved,
                quantity_available=item.quantity_available,
                low_stock_threshold=item.low_stock_threshold,
                is_in_stock=item.is_in_stock,
                is_low_stock=item.is_low_stock,
                is_active=item.variant.is_active,
                updated_at=item.updated_at,
            )
            for item in items
        ]

    @staticmethod
    async def get_inventory_item(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID] = None,
    ) -> SellerInventoryItemResponse:
        """Fetch variant inventory item with ownership check."""
        variant, product = await SellerService.get_variant_by_id(db, variant_id, seller_id)
        inv = await InventoryService.get_by_variant_id(db, variant_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record for variant '{variant_id}' not found.",
            )
        return SellerInventoryItemResponse(
            id=inv.id,
            variant_id=inv.variant_id,
            product_id=product.id,
            product_name=product.name,
            sku=variant.sku,
            color=variant.color,
            size=variant.size,
            price=variant.price,
            compare_at_price=variant.compare_at_price,
            quantity_on_hand=inv.quantity_on_hand,
            quantity_reserved=inv.quantity_reserved,
            quantity_available=inv.quantity_available,
            low_stock_threshold=inv.low_stock_threshold,
            is_in_stock=inv.is_in_stock,
            is_low_stock=inv.is_low_stock,
            is_active=variant.is_active,
            updated_at=inv.updated_at,
        )

    @staticmethod
    async def set_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        quantity_on_hand: Optional[int] = None,
        low_stock_threshold: Optional[int] = None,
    ) -> SellerInventoryItemResponse:
        """Set stock quantity or threshold via InventoryService under row-level lock."""
        await SellerService.get_variant_by_id(db, variant_id, seller_id)
        await InventoryService.set_stock(
            db=db,
            variant_id=variant_id,
            quantity_on_hand=quantity_on_hand,
            low_stock_threshold=low_stock_threshold,
        )
        return await SellerService.get_inventory_item(db, variant_id, seller_id)

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        seller_id: Optional[uuid.UUID],
        adjustment: int,
        reason: Optional[str] = None,
    ) -> SellerInventoryItemResponse:
        """Adjust stock delta via InventoryService under row-level lock."""
        await SellerService.get_variant_by_id(db, variant_id, seller_id)
        await InventoryService.adjust_stock(
            db=db,
            variant_id=variant_id,
            adjustment=adjustment,
            reason=reason,
        )
        return await SellerService.get_inventory_item(db, variant_id, seller_id)

    # ==========================================================================
    # Seller Order Visibility
    # ==========================================================================

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        seller_id: Optional[uuid.UUID] = None,
        status_filter: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SellerOrderResponse]:
        """
        List orders containing items belonging to the seller.
        Orders and items belonging to other sellers are strictly filtered out.
        No sensitive customer or payment details are exposed.
        """
        stmt = (
            select(Order)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .outerjoin(ProductVariant, OrderItem.variant_id == ProductVariant.id)
            .outerjoin(Product, ProductVariant.product_id == Product.id)
        )
        if seller_id is not None:
            stmt = stmt.where((OrderItem.seller_id == seller_id) | (Product.seller_id == seller_id))
        if status_filter is not None:
            stmt = stmt.where(Order.status == status_filter)

        stmt = (
            stmt.distinct()
            .options(
                selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
                selectinload(Order.sub_orders).selectinload(SubOrder.items),
                selectinload(Order.payment),
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        orders = list(res.scalars().all())

        seller_orders: List[SellerOrderResponse] = []
        for ord_entity in orders:
            # Find sub_order matching this seller if exists
            matched_so = None
            if seller_id is not None and ord_entity.sub_orders:
                matched_so = next((so for so in ord_entity.sub_orders if so.seller_id == seller_id), None)
            elif ord_entity.sub_orders:
                matched_so = ord_entity.sub_orders[0]

            seller_items: List[SellerOrderItemResponse] = []
            subtotal = Decimal("0.00")
            qty = 0
            for item in ord_entity.items:
                is_seller_item = (
                    (item.seller_id is not None and (seller_id is None or item.seller_id == seller_id))
                    or (
                        item.variant is not None
                        and item.variant.product is not None
                        and (seller_id is None or item.variant.product.seller_id == seller_id)
                    )
                )
                if is_seller_item:
                    seller_items.append(
                        SellerOrderItemResponse(
                            id=item.id,
                            order_id=item.order_id,
                            sub_order_id=item.sub_order_id,
                            seller_id=item.seller_id,
                            variant_id=item.variant_id,
                            product_name=item.product_name,
                            sku=item.sku,
                            color=item.variant.color if item.variant else None,
                            size=item.variant.size if item.variant else None,
                            unit_price=item.unit_price,
                            quantity=item.quantity,
                            line_total=item.line_total,
                            created_at=item.created_at,
                        )
                    )
                    subtotal += item.line_total
                    qty += item.quantity

            if seller_items:
                payment_st = None
                if ord_entity.payment:
                    p = ord_entity.payment
                    payment_st = p.status.value if hasattr(p.status, "value") else str(p.status)

                status_val = matched_so.status if matched_so else ord_entity.status

                seller_orders.append(
                    SellerOrderResponse(
                        id=ord_entity.id,
                        order_number=ord_entity.order_number,
                        sub_order_id=matched_so.id if matched_so else None,
                        sub_order_number=matched_so.sub_order_number if matched_so else ord_entity.order_number,
                        created_at=ord_entity.created_at,
                        status=status_val,
                        currency=ord_entity.currency,
                        seller_subtotal=matched_so.subtotal if matched_so else subtotal,
                        seller_total_quantity=qty,
                        payment_status=payment_st,
                        carrier=matched_so.carrier if matched_so else None,
                        tracking_number=matched_so.tracking_number if matched_so else None,
                        shipped_at=matched_so.shipped_at if matched_so else None,
                        delivered_at=matched_so.delivered_at if matched_so else None,
                        items=seller_items,
                    )
                )

        return seller_orders

    @staticmethod
    async def get_order(
        db: AsyncSession,
        order_id: uuid.UUID,
        seller_id: Optional[uuid.UUID] = None,
    ) -> SellerOrderResponse:
        """
        Fetch order details filtered strictly to the seller's items.
        Allows lookup by parent order_id OR sub_order_id.
        If order exists but contains zero items for this seller, returns 404 (IDOR protection).
        """
        # 1. Try finding by parent order id
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
                selectinload(Order.sub_orders).selectinload(SubOrder.items),
                selectinload(Order.payment),
            )
        )
        res = await db.execute(stmt)
        ord_entity = res.scalar_one_or_none()

        # 2. If not found by parent Order ID, check if order_id is actually a SubOrder ID
        if not ord_entity:
            so_stmt = select(SubOrder).where(SubOrder.id == order_id)
            so_res = await db.execute(so_stmt)
            sub_order_match = so_res.scalar_one_or_none()
            if sub_order_match:
                stmt = (
                    select(Order)
                    .where(Order.id == sub_order_match.order_id)
                    .options(
                        selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
                        selectinload(Order.sub_orders).selectinload(SubOrder.items),
                        selectinload(Order.payment),
                    )
                )
                res = await db.execute(stmt)
                ord_entity = res.scalar_one_or_none()

        if not ord_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id '{order_id}' not found.",
            )

        matched_so = None
        if seller_id is not None and ord_entity.sub_orders:
            matched_so = next((so for so in ord_entity.sub_orders if so.seller_id == seller_id), None)
        elif ord_entity.sub_orders:
            matched_so = ord_entity.sub_orders[0]

        seller_items: List[SellerOrderItemResponse] = []
        subtotal = Decimal("0.00")
        qty = 0
        for item in ord_entity.items:
            is_seller_item = (
                (item.seller_id is not None and (seller_id is None or item.seller_id == seller_id))
                or (
                    item.variant is not None
                    and item.variant.product is not None
                    and (seller_id is None or item.variant.product.seller_id == seller_id)
                )
            )
            if is_seller_item:
                seller_items.append(
                    SellerOrderItemResponse(
                        id=item.id,
                        order_id=item.order_id,
                        sub_order_id=item.sub_order_id,
                        seller_id=item.seller_id,
                        variant_id=item.variant_id,
                        product_name=item.product_name,
                        sku=item.sku,
                        color=item.variant.color if item.variant else None,
                        size=item.variant.size if item.variant else None,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        line_total=item.line_total,
                        created_at=item.created_at,
                    )
                )
                subtotal += item.line_total
                qty += item.quantity

        if not seller_items and seller_id is not None:
            # Order contains no items for this seller
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id '{order_id}' not found.",
            )

        payment_st = None
        if ord_entity.payment:
            p = ord_entity.payment
            payment_st = p.status.value if hasattr(p.status, "value") else str(p.status)

        status_val = matched_so.status if matched_so else ord_entity.status

        return SellerOrderResponse(
            id=ord_entity.id,
            order_number=ord_entity.order_number,
            sub_order_id=matched_so.id if matched_so else None,
            sub_order_number=matched_so.sub_order_number if matched_so else ord_entity.order_number,
            created_at=ord_entity.created_at,
            status=status_val,
            currency=ord_entity.currency,
            seller_subtotal=matched_so.subtotal if matched_so else subtotal,
            seller_total_quantity=qty,
            payment_status=payment_st,
            carrier=matched_so.carrier if matched_so else None,
            tracking_number=matched_so.tracking_number if matched_so else None,
            shipped_at=matched_so.shipped_at if matched_so else None,
            delivered_at=matched_so.delivered_at if matched_so else None,
            items=seller_items,
        )

    @staticmethod
    async def update_fulfillment(
        db: AsyncSession,
        sub_order_id: uuid.UUID,
        seller_id: Optional[uuid.UUID] = None,
        new_status: Optional[OrderStatus] = None,
        carrier: Optional[str] = None,
        tracking_number: Optional[str] = None,
    ) -> SellerOrderResponse:
        """
        Update fulfillment details (status, carrier, tracking number) for a vendor sub-order.
        Enforces vendor ownership and controlled lifecycle status transitions:
        CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED.
        """
        stmt = (
            select(SubOrder)
            .where(SubOrder.id == sub_order_id)
            .options(
                selectinload(SubOrder.items),
                selectinload(SubOrder.order).selectinload(Order.sub_orders),
                selectinload(SubOrder.order).selectinload(Order.payment),
            )
        )
        res = await db.execute(stmt)
        sub_order = res.scalar_one_or_none()

        # If not found by sub_order_id directly, try finding if sub_order_id passed was order_id
        if not sub_order:
            order_stmt = (
                select(SubOrder)
                .where(SubOrder.order_id == sub_order_id)
                .options(
                    selectinload(SubOrder.items),
                    selectinload(SubOrder.order).selectinload(Order.sub_orders),
                    selectinload(SubOrder.order).selectinload(Order.payment),
                )
            )
            if seller_id is not None:
                order_stmt = order_stmt.where(SubOrder.seller_id == seller_id)
            sub_order = (await db.execute(order_stmt)).scalar_one_or_none()

        if not sub_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SubOrder with id '{sub_order_id}' not found.",
            )

        if seller_id is not None and sub_order.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage this sub-order.",
            )

        now = datetime.now(timezone.utc)

        if carrier is not None:
            sub_order.carrier = carrier.strip() if carrier.strip() else None
        if tracking_number is not None:
            sub_order.tracking_number = tracking_number.strip() if tracking_number.strip() else None

        if new_status is not None and new_status != sub_order.status:
            # Validate status transition
            valid_transitions = {
                OrderStatus.PENDING_PAYMENT: [OrderStatus.CANCELLED],
                OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
                OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
                OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
                OrderStatus.DELIVERED: [],
                OrderStatus.CANCELLED: [],
            }
            allowed = valid_transitions.get(sub_order.status, [])
            if new_status not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from '{sub_order.status.value}' to '{new_status.value}'.",
                )

            sub_order.status = new_status
            if new_status == OrderStatus.SHIPPED and not sub_order.shipped_at:
                sub_order.shipped_at = now
            elif new_status == OrderStatus.DELIVERED and not sub_order.delivered_at:
                sub_order.delivered_at = now

        sub_order.updated_at = now

        # Update parent order global status if applicable
        parent = sub_order.order
        if parent and parent.sub_orders:
            all_statuses = [so.status for so in parent.sub_orders if so.id != sub_order.id] + [sub_order.status]
            if all(s == OrderStatus.DELIVERED for s in all_statuses):
                parent.status = OrderStatus.DELIVERED
                parent.updated_at = now
            elif all(s in (OrderStatus.SHIPPED, OrderStatus.DELIVERED) for s in all_statuses):
                parent.status = OrderStatus.SHIPPED
                parent.updated_at = now
            elif any(s == OrderStatus.PROCESSING for s in all_statuses) and parent.status == OrderStatus.CONFIRMED:
                parent.status = OrderStatus.PROCESSING
                parent.updated_at = now

        await db.commit()
        await db.refresh(sub_order)

        # Return updated seller order response
        return await SellerService.get_order(db, sub_order.order_id, seller_id)

    # ==========================================================================
    # Store Profile Management (Phase 9B.1)
    # ==========================================================================

    @staticmethod
    async def get_or_create_store(
        db: AsyncSession,
        seller_id: uuid.UUID,
    ) -> Store:
        """
        Retrieve existing store or lazily provision one for the seller.
        Rules:
        1. If store exists, return it.
        2. If not, create automatically with initial store name = first_name + last_name
           or fallback 'seller-{short_id}'.
        3. Deterministic collision resolution for store_name and slug.
        4. Initial status = ACTIVE, is_verified = False.
        5. Safe under concurrent requests via database uniqueness & rollback.
        """
        stmt = select(Store).where(Store.seller_id == seller_id)
        result = await db.execute(stmt)
        store = result.scalar_one_or_none()
        if store:
            return store

        # Retrieve user to derive initial name
        user = await db.get(User, seller_id)
        parts = [p.strip() for p in [(user.first_name if user else ""), (user.last_name if user else "")] if p and p.strip()]
        base_name = " ".join(parts).strip() if parts else f"seller-{str(seller_id)[:8]}"

        # Resolve store_name collision deterministically
        candidate_name = base_name
        name_counter = 1
        while True:
            existing_name = await db.execute(select(Store.id).where(Store.store_name == candidate_name))
            if not existing_name.scalar_one_or_none():
                break
            name_counter += 1
            candidate_name = f"{base_name} {name_counter}"

        # Generate unique slug
        slug = await generate_unique_slug(db, candidate_name)

        new_store = Store(
            id=uuid.uuid4(),
            seller_id=seller_id,
            store_name=candidate_name,
            slug=slug,
            status=StoreStatus.ACTIVE,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_store)
        try:
            await db.commit()
            await db.refresh(new_store)
            return new_store
        except IntegrityError:
            await db.rollback()
            # Handle concurrent creation
            stmt = select(Store).where(Store.seller_id == seller_id)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            raise

    @staticmethod
    async def update_store_profile(
        db: AsyncSession,
        seller_id: uuid.UUID,
        payload: SellerProfileUpdate,
    ) -> Store:
        """
        Update seller store profile fields with strict validation.
        Seller may modify store_name, slug, bio, contact_email, contact_phone.
        Seller CANNOT modify seller_id, status, is_verified.
        """
        store = await SellerService.get_or_create_store(db, seller_id)

        # 1. Update store_name if provided
        if payload.store_name is not None and payload.store_name.strip() != store.store_name:
            new_name = payload.store_name.strip()
            # Check uniqueness against other stores
            dup_stmt = select(Store.id).where(Store.store_name == new_name, Store.id != store.id)
            dup = (await db.execute(dup_stmt)).scalar_one_or_none()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Store name '{new_name}' is already taken.",
                )
            store.store_name = new_name

        # 2. Update slug if provided
        if payload.slug is not None and payload.slug.strip() != store.slug:
            new_slug = payload.slug.strip().lower()
            if not is_valid_slug(new_slug):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Slug '{new_slug}' is invalid or reserved. Allowed format: ^[a-z0-9]+(?:-[a-z0-9]+)*$, 3-120 chars.",
                )
            dup_slug_stmt = select(Store.id).where(Store.slug == new_slug, Store.id != store.id)
            dup_slug = (await db.execute(dup_slug_stmt)).scalar_one_or_none()
            if dup_slug:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Slug '{new_slug}' is already taken.",
                )
            store.slug = new_slug

        # 3. Update optional narrative & contact fields
        if payload.bio is not None:
            store.bio = payload.bio.strip() if payload.bio else None
        if payload.contact_email is not None:
            store.contact_email = payload.contact_email.strip() if payload.contact_email else None
        if payload.contact_phone is not None:
            store.contact_phone = payload.contact_phone.strip() if payload.contact_phone else None

        store.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(store)
        return store

    @staticmethod
    async def upload_store_logo(
        db: AsyncSession,
        seller_id: uuid.UUID,
        file_content: bytes,
        filename: Optional[str],
        content_type: Optional[str],
    ) -> StoreMediaUploadResponse:
        """
        Upload store logo with strict validation (max 5MB, JPEG/PNG/WebP, magic bytes).
        Replaces previous logo and deletes old MinIO object cleanly after success.
        """
        MAX_LOGO_SIZE = 5 * 1024 * 1024
        if len(file_content) > MAX_LOGO_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logo file exceeds maximum allowed size of 5MB.",
            )

        ext = validate_image_file(file_content, filename, content_type)
        object_key = f"stores/{seller_id}/logo/{uuid.uuid4().hex}{ext}"

        store = await SellerService.get_or_create_store(db, seller_id)
        old_object_key = store.logo_object_key

        # Upload new object
        url = StorageService.upload_file(
            data=file_content,
            object_key=object_key,
            content_type=content_type or "image/jpeg",
        )

        store.logo_url = url
        store.logo_object_key = object_key
        store.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(store)

        # Delete previous object if existed
        if old_object_key and old_object_key != object_key:
            StorageService.delete_file(old_object_key)

        return StoreMediaUploadResponse(url=url, object_key=object_key)

    @staticmethod
    async def upload_store_banner(
        db: AsyncSession,
        seller_id: uuid.UUID,
        file_content: bytes,
        filename: Optional[str],
        content_type: Optional[str],
    ) -> StoreMediaUploadResponse:
        """
        Upload store banner with strict validation (max 10MB, JPEG/PNG/WebP, magic bytes).
        Replaces previous banner and deletes old MinIO object cleanly after success.
        """
        MAX_BANNER_SIZE = 10 * 1024 * 1024
        if len(file_content) > MAX_BANNER_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Banner file exceeds maximum allowed size of 10MB.",
            )

        ext = validate_image_file(file_content, filename, content_type)
        object_key = f"stores/{seller_id}/banner/{uuid.uuid4().hex}{ext}"

        store = await SellerService.get_or_create_store(db, seller_id)
        old_object_key = store.banner_object_key

        # Upload new object
        url = StorageService.upload_file(
            data=file_content,
            object_key=object_key,
            content_type=content_type or "image/jpeg",
        )

        store.banner_url = url
        store.banner_object_key = object_key
        store.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(store)

        # Delete previous object if existed
        if old_object_key and old_object_key != object_key:
            StorageService.delete_file(old_object_key)

        return StoreMediaUploadResponse(url=url, object_key=object_key)
