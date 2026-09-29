from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.cart.enums import CartStatus
from app.modules.cart.models import Cart, CartItem
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem
from app.modules.orders.enums import OrderStatus
from app.modules.orders.models import Order, OrderItem


class CheckoutService:
    """Atomic transactional checkout coordinator."""

    @staticmethod
    async def checkout(
        db: AsyncSession,
        customer_id: uuid.UUID,
    ) -> Order:
        """
        Execute atomic checkout for the customer's active cart.
        Locks inventory rows, revalidates stock and catalog state, applies authoritative prices,
        creates Order with historical snapshots, decrements inventory, and marks cart CHECKED_OUT.
        """
        # 1. Fetch active cart with full item details
        cart_stmt = (
            select(Cart)
            .where(Cart.customer_id == customer_id, Cart.status == CartStatus.ACTIVE)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product),
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.inventory),
            )
        )
        cart_res = await db.execute(cart_stmt)
        cart = cart_res.scalar_one_or_none()

        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot checkout with an empty cart.",
            )

        # 2. Sort items by variant_id to guarantee deterministic lock acquisition order (prevents deadlocks)
        sorted_cart_items = sorted(cart.items, key=lambda i: str(i.variant_id))

        order_subtotal = Decimal("0.00")
        processed_items = []

        # 3. Process each item: acquire row lock and revalidate
        for cart_item in sorted_cart_items:
            # Row-level lock on inventory record
            inv_stmt = (
                select(InventoryItem)
                .where(InventoryItem.variant_id == cart_item.variant_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            inv_res = await db.execute(inv_stmt)
            inventory = inv_res.scalar_one_or_none()
            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Inventory record for variant '{cart_item.variant_id}' not found.",
                )

            variant = cart_item.variant
            if not variant or not variant.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Variant '{cart_item.variant_id}' is no longer active.",
                )

            product = variant.product
            if not product or product.status != ProductStatus.ACTIVE or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name if product else cart_item.variant_id}' is no longer available for purchase.",
                )

            # Available stock check
            available_qty = inventory.quantity_available
            if cart_item.quantity > available_qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for '{product.name}' ({variant.sku}). "
                        f"Requested {cart_item.quantity}, available {available_qty}."
                    ),
                )

            # Commerce rule: Use current authoritative price from ProductVariant
            current_unit_price = Decimal(str(variant.price))
            line_total = current_unit_price * Decimal(str(cart_item.quantity))
            order_subtotal += line_total

            # Decrement inventory quantity on hand
            inventory.quantity_on_hand -= cart_item.quantity
            inventory.updated_at = datetime.now(timezone.utc)

            processed_items.append({
                "variant_id": variant.id,
                "product_name": product.name,
                "sku": variant.sku,
                "unit_price": current_unit_price,
                "quantity": cart_item.quantity,
                "line_total": line_total,
            })

        # 4. Generate unique human-readable order number
        now = datetime.now(timezone.utc)
        order_number = f"ORD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 5. Create Order
        order = Order(
            id=uuid.uuid4(),
            customer_id=customer_id,
            order_number=order_number,
            status=OrderStatus.PENDING_PAYMENT,
            subtotal=order_subtotal,
            total=order_subtotal,
            currency="USD",
            created_at=now,
            updated_at=now,
        )
        db.add(order)

        # 6. Create OrderItems with immutable historical snapshots
        for item_info in processed_items:
            order_item = OrderItem(
                id=uuid.uuid4(),
                order_id=order.id,
                variant_id=item_info["variant_id"],
                product_name=item_info["product_name"],
                sku=item_info["sku"],
                unit_price=item_info["unit_price"],
                quantity=item_info["quantity"],
                line_total=item_info["line_total"],
                created_at=now,
            )
            db.add(order_item)

        # 7. Transition cart status to CHECKED_OUT
        cart.status = CartStatus.CHECKED_OUT
        cart.updated_at = now

        # 8. Commit atomic transaction
        await db.commit()

        # 9. Return fresh order with preloaded items
        reload_stmt = (
            select(Order)
            .where(Order.id == order.id)
            .options(selectinload(Order.items))
        )
        reload_res = await db.execute(reload_stmt)
        return reload_res.scalar_one()


class OrderService:
    """Service layer managing customer order history and queries."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        order_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Optional[Order]:
        """Fetch customer order by ID, enforcing customer ownership."""
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.customer_id == customer_id)
            .options(selectinload(Order.items))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_customer_orders(
        db: AsyncSession,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Order]:
        """List past orders belonging to the customer."""
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
