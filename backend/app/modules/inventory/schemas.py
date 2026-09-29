from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InventoryResponse(BaseModel):
    """Detailed inventory status for a specific SKU/variant (Seller / Admin view)."""

    id: uuid.UUID
    variant_id: uuid.UUID
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    low_stock_threshold: int
    is_in_stock: bool
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryUpdate(BaseModel):
    """Payload to directly update stock levels or threshold."""

    quantity_on_hand: Optional[int] = Field(
        default=None,
        ge=0,
        description="Absolute physical quantity available on hand (must be >= 0)",
    )
    low_stock_threshold: Optional[int] = Field(
        default=None,
        ge=0,
        description="Threshold below or at which variant is considered low stock (must be >= 0)",
    )


class InventoryAdjustRequest(BaseModel):
    """Payload to adjust quantity on hand by a positive or negative delta."""

    adjustment: int = Field(
        ...,
        description="Signed integer delta to apply to quantity_on_hand (+/-)",
    )
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional audit reason for the stock adjustment (e.g. 'restock', 'damage', 'correction')",
    )


class PublicVariantStockResponse(BaseModel):
    """Public customer-facing stock availability without revealing internal quantity numbers."""

    variant_id: uuid.UUID
    is_in_stock: bool

    model_config = ConfigDict(from_attributes=True)
