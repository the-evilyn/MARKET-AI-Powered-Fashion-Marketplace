from datetime import datetime
from decimal import Decimal
import uuid
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, model_validator

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
    payment_status: Optional[str] = None
    payment_provider: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_payment_fields(cls, data: Any) -> Any:
        if hasattr(data, "payment") and getattr(data, "payment", None):
            p = data.payment
            p_status = p.status.value if hasattr(p.status, "value") else str(p.status)
            p_provider = p.provider.value if hasattr(p.provider, "value") else str(p.provider)
            return {
                "id": data.id,
                "customer_id": data.customer_id,
                "order_number": data.order_number,
                "status": data.status,
                "subtotal": data.subtotal,
                "total": data.total,
                "currency": data.currency,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "items": data.items or [],
                "payment_status": p_status,
                "payment_provider": p_provider,
            }
        return data
