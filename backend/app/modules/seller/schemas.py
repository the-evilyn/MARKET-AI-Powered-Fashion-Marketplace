from datetime import datetime
from decimal import Decimal
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.enums import OrderStatus


class SellerDashboardResponse(BaseModel):
    """Basic seller dashboard KPIs."""
    total_products: int = Field(..., description="Total count of products owned by the seller")
    active_products: int = Field(..., description="Count of active products owned by the seller")
    total_variants: int = Field(..., description="Total count of SKU variants across seller products")
    low_stock_variants: int = Field(..., description="Count of variants at or below low stock threshold")
    out_of_stock_variants: int = Field(..., description="Count of variants with zero available inventory")
    total_orders: int = Field(..., description="Total count of distinct orders containing seller products")
    pending_orders: int = Field(..., description="Count of pending orders containing seller products")
    confirmed_orders: int = Field(..., description="Count of confirmed/paid orders containing seller products")
    cancelled_orders: int = Field(..., description="Count of cancelled orders containing seller products")
    total_sales: Decimal = Field(..., description="Total monetary sales from confirmed orders (USD)")
    total_items_sold: int = Field(..., description="Total item units sold in confirmed orders")

    model_config = ConfigDict(from_attributes=True)


class SellerInventoryItemResponse(BaseModel):
    """Enriched variant inventory view for seller management."""
    id: uuid.UUID
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    low_stock_threshold: int
    is_in_stock: bool
    is_low_stock: bool
    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SellerOrderItemResponse(BaseModel):
    """Historical snapshot of an order item belonging to the seller."""
    id: uuid.UUID
    order_id: uuid.UUID
    sub_order_id: Optional[uuid.UUID] = None
    seller_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    product_name: str
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SellerFulfillmentRequest(BaseModel):
    """Payload for updating seller sub-order fulfillment status and tracking."""
    status: Optional[OrderStatus] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None


class SellerOrderResponse(BaseModel):
    """Seller-scoped order response containing only the seller's items and fulfillment tracking."""
    id: uuid.UUID
    order_number: str
    sub_order_id: Optional[uuid.UUID] = None
    sub_order_number: Optional[str] = None
    created_at: datetime
    status: OrderStatus
    currency: str
    seller_subtotal: Decimal
    seller_total_quantity: int
    payment_status: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[SellerOrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

