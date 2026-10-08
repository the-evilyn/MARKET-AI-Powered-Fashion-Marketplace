from datetime import datetime
from decimal import Decimal
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PublicStoreResponse(BaseModel):
    """Publicly visible store profile metadata."""
    store_name: str
    slug: str
    bio: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    contact_email: Optional[str] = None
    is_verified: bool
    created_at: datetime
    active_products_count: int

    model_config = ConfigDict(from_attributes=True)


class PublicStoreProductItem(BaseModel):
    """Public product summary scoped to a store catalog."""
    id: uuid.UUID
    name: str
    slug: str
    base_price: Decimal
    currency: str = "USD"
    brand_name: Optional[str] = None
    category_name: Optional[str] = None
    primary_image_url: Optional[str] = None
    is_in_stock: bool
    variants_count: int

    model_config = ConfigDict(from_attributes=True)


class PublicStoreProductsResponse(BaseModel):
    """Paginated collection of public products belonging to a store."""
    items: List[PublicStoreProductItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
