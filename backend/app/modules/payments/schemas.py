from datetime import datetime
from decimal import Decimal
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.enums import OrderStatus
from app.modules.payments.enums import PaymentProvider, PaymentStatus


class PayPalCreateOrderRequest(BaseModel):
    """Payload to initiate a PayPal payment for an existing customer order."""
    order_id: uuid.UUID = Field(..., description="Internal ID of the PENDING_PAYMENT order")


class PayPalCreateOrderResponse(BaseModel):
    """Client-safe PayPal payment initialization response."""
    payment_id: uuid.UUID
    paypal_order_id: str
    amount: Decimal
    currency: str
    provider: str

    model_config = ConfigDict(from_attributes=True)


class PayPalCaptureRequest(BaseModel):
    """Payload to capture an authorized PayPal order payment."""
    paypal_order_id: str = Field(..., min_length=1, max_length=128, description="PayPal Order ID")


class PayPalCaptureResponse(BaseModel):
    """Authoritative result after server-side PayPal payment capture."""
    payment_id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    status: PaymentStatus
    order_status: OrderStatus
    provider_order_id: str
    provider_payment_id: Optional[str] = None
    amount: Decimal
    currency: str

    model_config = ConfigDict(from_attributes=True)


class PayPalCancelRequest(BaseModel):
    """Payload when customer cancels payment on PayPal checkout."""
    paypal_order_id: str = Field(..., min_length=1, max_length=128, description="PayPal Order ID")


class PayPalCancelResponse(BaseModel):
    """Result of cancelled payment release."""
    payment_id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    status: PaymentStatus
    order_status: OrderStatus

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    """Payment record detail schema."""
    id: uuid.UUID
    order_id: uuid.UUID
    provider: PaymentProvider
    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    status: PaymentStatus
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookProcessResponse(BaseModel):
    """Status report for asynchronous payment webhook ingestion."""
    status: str
    detail: Optional[str] = None
