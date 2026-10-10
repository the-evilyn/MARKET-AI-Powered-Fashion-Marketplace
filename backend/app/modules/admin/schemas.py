from datetime import datetime
from decimal import Decimal
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.enums import OrderStatus
from app.modules.payments.enums import PaymentProvider, PaymentStatus
from app.modules.seller.enums import StoreStatus
from app.modules.users.enums import UserRole


# ==============================================================================
# Admin Dashboard Schemas
# ==============================================================================

class AdminCurrencySalesResponse(BaseModel):
    """Paid revenue totals for a specific currency."""
    currency: str = Field(..., description="ISO 4217 currency code (e.g. USD)")
    total_sales: Decimal = Field(..., description="Total completed revenue in this currency")
    order_count: int = Field(..., description="Count of paid orders in this currency")

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardResponse(BaseModel):
    """Comprehensive marketplace KPI metrics derived from real database models."""
    total_users: int = Field(..., description="Total registered users across all roles")
    active_users: int = Field(..., description="Count of currently active users")
    total_sellers: int = Field(..., description="Total users registered with SELLER role")
    active_sellers: int = Field(..., description="Active users with SELLER role")
    total_stores: int = Field(..., description="Total storefronts provisioned on the platform")
    stores_awaiting_review: int = Field(..., description="Stores with PENDING status awaiting moderation")
    verified_stores: int = Field(..., description="Stores with is_verified = True")
    total_orders: int = Field(..., description="Total orders created across all customers")
    orders_by_status: Dict[str, int] = Field(..., description="Order count breakdown by OrderStatus")
    sales_by_currency: List[AdminCurrencySalesResponse] = Field(
        default_factory=list,
        description="Completed sales totals grouped by currency (strictly completed payments)",
    )
    total_paid_orders: int = Field(
        ...,
        description="Total distinct orders with confirmed and completed payment",
    )

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Admin User Management Schemas
# ==============================================================================

class AdminUserSummaryResponse(BaseModel):
    """Safe user summary without password hashes or private credentials."""
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserDetailResponse(AdminUserSummaryResponse):
    """Enriched user detail with associated storefront if seller."""
    store_id: Optional[uuid.UUID] = None
    store_name: Optional[str] = None
    store_slug: Optional[str] = None


class AdminUserListResponse(BaseModel):
    """Paginated collection of users."""
    items: List[AdminUserSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class AdminUserStatusUpdate(BaseModel):
    """Update activation status of a user account."""
    is_active: bool = Field(..., description="Whether the account is enabled or disabled")

    model_config = ConfigDict(extra="forbid")


# ==============================================================================
# Admin Store Moderation Schemas
# ==============================================================================

class AdminStoreSummaryResponse(BaseModel):
    """Store summary for moderation lists."""
    id: uuid.UUID
    seller_id: uuid.UUID
    store_name: str
    slug: str
    bio: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: StoreStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    seller_email: Optional[str] = None
    seller_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminStoreDetailResponse(AdminStoreSummaryResponse):
    """Enriched store detail with product statistics."""
    active_products_count: int = Field(0, description="Count of active and published products")
    total_products_count: int = Field(0, description="Total products created by this store")


class AdminStoreListResponse(BaseModel):
    """Paginated collection of stores for admin moderation."""
    items: List[AdminStoreSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class AdminStoreModerationUpdate(BaseModel):
    """Moderation payload for updating store verification or operational status."""
    is_verified: Optional[bool] = Field(None, description="Set trusted seller verification badge")
    status: Optional[StoreStatus] = Field(None, description="Update store operational status")

    model_config = ConfigDict(extra="forbid")


# ==============================================================================
# Admin Orders Schemas
# ==============================================================================

class AdminOrderItemResponse(BaseModel):
    """Snapshot line item summary for admin view."""
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


class AdminSubOrderResponse(BaseModel):
    """Vendor-scoped sub-order fulfillment partition."""
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    seller_email: Optional[str] = None
    sub_order_number: str
    status: OrderStatus
    subtotal: Decimal
    shipping_amount: Decimal
    total: Decimal
    currency: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    items: List[AdminOrderItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentSummaryResponse(BaseModel):
    """Safe payment metadata excluding credentials or secrets."""
    id: uuid.UUID
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal
    currency: str
    provider_payment_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderSummaryResponse(BaseModel):
    """Order summary for admin listings across all customers and sellers."""
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    status: OrderStatus
    subtotal: Decimal
    total: Decimal
    currency: str
    payment_status: Optional[PaymentStatus] = None
    sub_orders_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderDetailResponse(BaseModel):
    """Complete order detail with customer, payment, sub-orders, and line items."""
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    status: OrderStatus
    subtotal: Decimal
    total: Decimal
    currency: str
    payment: Optional[AdminPaymentSummaryResponse] = None
    sub_orders: List[AdminSubOrderResponse] = Field(default_factory=list)
    items: List[AdminOrderItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderListResponse(BaseModel):
    """Paginated collection of orders."""
    items: List[AdminOrderSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
