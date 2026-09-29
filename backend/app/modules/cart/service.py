from datetime import datetime, timezone
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.cart.enums import CartStatus
from app.modules.cart.models import Cart, CartItem
from app.modules.cart.schemas import CartItemCreate
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem


class CartService:
    """Service handling customer shopping cart persistence and validation."""

    @staticmethod
    async def _load_cart(db: AsyncSession, cart_id: uuid.UUID) -> Optional[Cart]:
        """Fetch cart by id with full variant, product, and inventory relations."""
        db.expire_all()
        stmt = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product),
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.inventory),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_or_create_active_cart(
        db: AsyncSession,
        customer_id: uuid.UUID,
    ) -> Cart:
        """Retrieve existing ACTIVE cart for the customer or create a new empty one."""
        stmt = (
            select(Cart)
            .where(Cart.customer_id == customer_id, Cart.status == CartStatus.ACTIVE)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product),
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.inventory),
            )
        )
        res = await db.execute(stmt)
        cart = res.scalar_one_or_none()
        if cart:
            return cart

        # Create new ACTIVE cart
        new_cart = Cart(
            id=uuid.uuid4(),
            customer_id=customer_id,
            status=CartStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_cart)
        await db.commit()
        return await CartService._load_cart(db, new_cart.id)  # type: ignore[return-value]

    @staticmethod
    async def add_item(
        db: AsyncSession,
        customer_id: uuid.UUID,
        payload: CartItemCreate,
    ) -> Cart:
        """Add a SKU variant to the customer's active cart or increment existing quantity."""
        cart = await CartService.get_or_create_active_cart(db, customer_id)

        # 1. Fetch variant with parent product and inventory
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.id == payload.variant_id)
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
                detail=f"Variant with id '{payload.variant_id}' not found.",
            )

        # 2. Validate product public purchasability
        product = variant.product
        if not product or product.status != ProductStatus.ACTIVE or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available for purchase.",
            )

        # 3. Validate variant is active
        if not variant.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product variant is not active.",
            )

        # 4. Validate inventory exists and stock is sufficient
        if not variant.inventory:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory record for variant does not exist.",
            )

        available_stock = variant.inventory.quantity_available

        # 5. Check if variant already exists in cart
        existing_item = next((item for item in cart.items if item.variant_id == variant.id), None)
        total_requested = payload.quantity + (existing_item.quantity if existing_item else 0)

        if total_requested > available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Requested quantity ({total_requested}) exceeds available stock ({available_stock})."
                ),
            )

        if existing_item:
            existing_item.quantity = total_requested
            existing_item.unit_price = variant.price
            existing_item.updated_at = datetime.now(timezone.utc)
        else:
            new_item = CartItem(
                id=uuid.uuid4(),
                cart_id=cart.id,
                variant_id=variant.id,
                quantity=payload.quantity,
                unit_price=variant.price,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_item)

        cart.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await CartService._load_cart(db, cart.id)  # type: ignore[return-value]

    @staticmethod
    async def update_item_quantity(
        db: AsyncSession,
        customer_id: uuid.UUID,
        item_id: uuid.UUID,
        quantity: int,
    ) -> Cart:
        """Update quantity of an existing item in the customer's active cart."""
        cart = await CartService.get_or_create_active_cart(db, customer_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id '{item_id}' not found in your active cart.",
            )

        stmt = (
            select(ProductVariant)
            .where(ProductVariant.id == item.variant_id)
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
                detail="Associated product variant no longer exists.",
            )

        product = variant.product
        if not product or product.status != ProductStatus.ACTIVE or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available for purchase.",
            )

        if not variant.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product variant is not active.",
            )

        if not variant.inventory or quantity > variant.inventory.quantity_available:
            avail = variant.inventory.quantity_available if variant.inventory else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({quantity}) exceeds available stock ({avail}).",
            )

        item.quantity = quantity
        item.unit_price = variant.price
        item.updated_at = datetime.now(timezone.utc)
        cart.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await CartService._load_cart(db, cart.id)  # type: ignore[return-value]

    @staticmethod
    async def remove_item(
        db: AsyncSession,
        customer_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> Cart:
        """Remove a single item from the customer's active cart."""
        cart = await CartService.get_or_create_active_cart(db, customer_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id '{item_id}' not found in your active cart.",
            )

        await db.delete(item)
        cart.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await CartService._load_cart(db, cart.id)  # type: ignore[return-value]

    @staticmethod
    async def clear_cart(
        db: AsyncSession,
        customer_id: uuid.UUID,
    ) -> Cart:
        """Remove all items from the customer's active cart. Cart remains ACTIVE."""
        cart = await CartService.get_or_create_active_cart(db, customer_id)
        for item in cart.items:
            await db.delete(item)
        cart.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await CartService._load_cart(db, cart.id)  # type: ignore[return-value]
