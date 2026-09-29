import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.catalog.enums import MediaType, ProductStatus


def slugify(text: str) -> str:
    """Generate a clean URL-safe slug."""
    text = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text)
    return slug.strip("-")


# ==============================================================================
# Brand Schemas
# ==============================================================================

class BrandCreate(BaseModel):
    """Payload to create a brand."""
    name: str = Field(min_length=1, max_length=150, description="Brand name")
    slug: Optional[str] = Field(default=None, max_length=160, description="Unique URL slug (auto-generated if omitted)")
    description: Optional[str] = Field(default=None, description="Brand narrative and details")
    logo_url: Optional[str] = Field(default=None, max_length=500, description="Brand logo URL or CDN path")
    is_active: bool = Field(default=True, description="Whether brand is publicly active")


class BrandUpdate(BaseModel):
    """Payload to update a brand."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    slug: Optional[str] = Field(default=None, max_length=160)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class BrandResponse(BaseModel):
    """Public brand representation."""
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Category Schemas
# ==============================================================================

class CategoryCreate(BaseModel):
    """Payload to create a category."""
    name: str = Field(min_length=1, max_length=150, description="Category name")
    slug: Optional[str] = Field(default=None, max_length=160, description="Unique URL slug (auto-generated if omitted)")
    description: Optional[str] = Field(default=None, description="Category description")
    parent_id: Optional[uuid.UUID] = Field(default=None, description="Parent category UUID for hierarchical grouping")
    is_active: bool = Field(default=True, description="Whether category is publicly active")


class CategoryUpdate(BaseModel):
    """Payload to update a category."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    slug: Optional[str] = Field(default=None, max_length=160)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Category representation."""
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Product Variant Schemas
# ==============================================================================

class ProductVariantCreate(BaseModel):
    """Payload to create a product variant SKU."""
    sku: str = Field(min_length=1, max_length=100, description="Unique merchant SKU code")
    color: Optional[str] = Field(default=None, max_length=50, description="Color name or code")
    size: Optional[str] = Field(default=None, max_length=50, description="Garment or shoe size")
    price: Decimal = Field(ge=Decimal("0.00"), description="Selling price (must be non-negative)")
    compare_at_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Original or strikethrough price")
    is_active: bool = Field(default=True, description="Whether SKU is active for sale")

    @model_validator(mode="after")
    def validate_compare_at_price(self) -> "ProductVariantCreate":
        if self.compare_at_price is not None and self.compare_at_price < self.price:
            raise ValueError("compare_at_price must be greater than or equal to price")
        return self


class ProductVariantUpdate(BaseModel):
    """Payload to update a product variant SKU."""
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, max_length=50)
    size: Optional[str] = Field(default=None, max_length=50)
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    compare_at_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_prices(self) -> "ProductVariantUpdate":
        if self.price is not None and self.compare_at_price is not None:
            if self.compare_at_price < self.price:
                raise ValueError("compare_at_price must be greater than or equal to price")
        return self


class ProductVariantResponse(BaseModel):
    """Product variant SKU representation."""
    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    is_active: bool
    is_in_stock: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Product Media Schemas
# ==============================================================================

class ProductMediaCreate(BaseModel):
    """Payload to register media asset metadata for a product."""
    media_type: MediaType = Field(default=MediaType.IMAGE, description="Media asset type (IMAGE, VIDEO, LOOKBOOK)")
    url: str = Field(min_length=1, max_length=500, description="Direct URL or CDN path to asset in object storage")
    object_key: Optional[str] = Field(default=None, max_length=255, description="MinIO/S3 object key")
    alt_text: Optional[str] = Field(default=None, max_length=255, description="Accessibility alt text")
    sort_order: int = Field(default=0, description="Display order sequence")
    is_primary: bool = Field(default=False, description="Whether this is the primary hero image")


class ProductMediaUpdate(BaseModel):
    """Payload to update media asset metadata."""
    media_type: Optional[MediaType] = None
    url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    object_key: Optional[str] = Field(default=None, max_length=255)
    alt_text: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = None
    is_primary: Optional[bool] = None


class ProductMediaResponse(BaseModel):
    """Product media asset representation."""
    id: uuid.UUID
    product_id: uuid.UUID
    media_type: MediaType
    url: str
    object_key: Optional[str] = None
    alt_text: Optional[str] = None
    sort_order: int
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Product Schemas
# ==============================================================================

class ProductCreate(BaseModel):
    """Payload to create a new product listing."""
    name: str = Field(min_length=1, max_length=255, description="Product title")
    slug: Optional[str] = Field(default=None, max_length=280, description="Unique URL slug (auto-generated if omitted)")
    description: Optional[str] = Field(default=None, description="Detailed garment narrative")
    brand_id: Optional[uuid.UUID] = Field(default=None, description="Associated brand UUID (optional for boutique/independent items)")
    category_id: Optional[uuid.UUID] = Field(default=None, description="Primary taxonomy category UUID")
    status: ProductStatus = Field(default=ProductStatus.DRAFT, description="Listing lifecycle status")
    base_price: Decimal = Field(ge=Decimal("0.00"), description="Base price (must be non-negative)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO-4217 3-letter currency code")
    is_active: bool = Field(default=True, description="Whether product is active")


class ProductUpdate(BaseModel):
    """Payload to update an existing product listing."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=280)
    description: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    status: Optional[ProductStatus] = None
    base_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Basic product listing representation."""
    id: uuid.UUID
    seller_id: uuid.UUID
    brand_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    status: ProductStatus
    base_price: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    """Detailed product representation with embedded brand, category, variants, and media."""
    brand: Optional[BrandResponse] = None
    category: Optional[CategoryResponse] = None
    variants: List[ProductVariantResponse] = []
    media: List[ProductMediaResponse] = []
