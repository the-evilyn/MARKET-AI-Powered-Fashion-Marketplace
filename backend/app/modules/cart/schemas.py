from datetime import datetime
from decimal import Decimal
import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.cart.enums import CartStatus


class CartItemCreate(BaseModel):
    """Payload to add a variant SKU to the customer cart."""
    variant_id: uuid.UUID = Field(..., description="Target ProductVariant UUID")
    quantity: int = Field(default=1, ge=1, description="Quantity of items to add (must be >= 1)")


class CartItemUpdate(BaseModel):
    """Payload to update the quantity of an existing cart item."""
    quantity: int = Field(..., ge=1, description="New quantity (must be >= 1)")


class CartItemResponse(BaseModel):
    """Customer-facing representation of a cart item with product details."""
    id: uuid.UUID
    cart_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    is_in_stock: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Customer-facing shopping cart representation with deterministic subtotals."""
    id: uuid.UUID
    customer_id: uuid.UUID
    status: CartStatus
    items: List[CartItemResponse] = []
    subtotal: Decimal = Decimal("0.00")
    item_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
