from datetime import datetime
from decimal import Decimal
import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.modules.orders.enums import OrderStatus


class OrderItemResponse(BaseModel):
    """Historical line item snapshot captured on the order."""
    id: uuid.UUID
    order_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    product_name: str
    sku: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Customer-facing order entity with items and authoritative totals."""
    id: uuid.UUID
    customer_id: uuid.UUID
    order_number: str
    status: OrderStatus
    subtotal: Decimal
    total: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
