import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem


class InventoryService:
    """Service handling stock mutations, queries, reservations, and concurrency locks."""

    @staticmethod
    async def get_by_variant_id(
        db: AsyncSession,
        variant_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[InventoryItem]:
        """Fetch InventoryItem by variant_id, optionally acquiring an exclusive row-level lock."""
        stmt = select(InventoryItem).where(InventoryItem.variant_id == variant_id)
        if for_update:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_for_variant(
        db: AsyncSession,
        variant_id: uuid.UUID,
        initial_quantity: int = 0,
        low_stock_threshold: int = 5,
        commit: bool = True,
    ) -> InventoryItem:
        """Create initial InventoryItem for a freshly created variant."""
        item = InventoryItem(
            id=uuid.uuid4(),
            variant_id=variant_id,
            quantity_on_hand=initial_quantity,
            quantity_reserved=0,
            low_stock_threshold=low_stock_threshold,
        )
        db.add(item)
        if commit:
            await db.commit()
            await db.refresh(item)
        return item

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        adjustment: int,
        reason: Optional[str] = None,
    ) -> InventoryItem:
        """
        Adjust quantity_on_hand by an integer delta (+/-).
        Uses row-level lock (with_for_update) to guarantee atomicity and prevent race conditions.
        """
        item = await InventoryService.get_by_variant_id(db, variant_id, for_update=True)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record for variant '{variant_id}' not found.",
            )

        new_on_hand = item.quantity_on_hand + adjustment
        if new_on_hand < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock adjustment rejected: quantity_on_hand cannot become negative.",
            )
        if new_on_hand < item.quantity_reserved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock adjustment rejected: new quantity ({new_on_hand}) cannot be less "
                    f"than reserved quantity ({item.quantity_reserved})."
                ),
            )

        item.quantity_on_hand = new_on_hand
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def set_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        quantity_on_hand: Optional[int] = None,
        low_stock_threshold: Optional[int] = None,
    ) -> InventoryItem:
        """
        Directly update stock quantity or threshold.
        Uses row-level lock (with_for_update) to prevent lost updates.
        """
        item = await InventoryService.get_by_variant_id(db, variant_id, for_update=True)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record for variant '{variant_id}' not found.",
            )

        if quantity_on_hand is not None:
            if quantity_on_hand < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity on hand cannot be negative.",
                )
            if quantity_on_hand < item.quantity_reserved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Quantity on hand ({quantity_on_hand}) cannot be less than "
                        f"currently reserved units ({item.quantity_reserved})."
                    ),
                )
            item.quantity_on_hand = quantity_on_hand

        if low_stock_threshold is not None:
            if low_stock_threshold < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Low stock threshold cannot be negative.",
                )
            item.low_stock_threshold = low_stock_threshold

        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def reserve_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        quantity: int,
    ) -> InventoryItem:
        """
        Reserve quantity for an incoming checkout order.
        Foundation method for Phase 4.
        """
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation quantity must be strictly positive.",
            )

        item = await InventoryService.get_by_variant_id(db, variant_id, for_update=True)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record for variant '{variant_id}' not found.",
            )

        if item.quantity_available < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock available: requested {quantity}, "
                    f"available {item.quantity_available}."
                ),
            )

        item.quantity_reserved += quantity
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def release_stock(
        db: AsyncSession,
        variant_id: uuid.UUID,
        quantity: int,
    ) -> InventoryItem:
        """
        Release previously reserved stock (e.g. cart expiration or cancellation).
        Foundation method for Phase 4.
        """
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Release quantity must be strictly positive.",
            )

        item = await InventoryService.get_by_variant_id(db, variant_id, for_update=True)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record for variant '{variant_id}' not found.",
            )

        if item.quantity_reserved < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot release {quantity} units: only "
                    f"{item.quantity_reserved} units are currently reserved."
                ),
            )

        item.quantity_reserved -= quantity
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_seller_inventory(
        db: AsyncSession,
        seller_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InventoryItem]:
        """
        List inventory records, filtered by seller ownership (if seller_id provided)
        and optional low stock filter.
        """
        stmt = (
            select(InventoryItem)
            .join(ProductVariant, InventoryItem.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
        )
        if seller_id is not None:
            stmt = stmt.where(Product.seller_id == seller_id)

        if low_stock_only:
            # quantity_on_hand - quantity_reserved <= low_stock_threshold
            stmt = stmt.where(
                (InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved)
                <= InventoryItem.low_stock_threshold
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
