import math
import uuid
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.enums import MediaType, ProductStatus


class SearchSort(str, Enum):
    """Allowed deterministic sorting options for search and catalog discovery."""

    relevance = "relevance"
    price_asc = "price_asc"
    price_desc = "price_desc"
    newest = "newest"
    oldest = "oldest"
    name_asc = "name_asc"
    name_desc = "name_desc"


class SearchQueryParams(BaseModel):
    """Decoupled query parameters for search operations."""

    q: Optional[str] = Field(default=None, description="Free-text search query term")
    category_id: Optional[uuid.UUID] = Field(default=None, description="Filter by category UUID")
    brand_id: Optional[uuid.UUID] = Field(default=None, description="Filter by brand UUID")
    min_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Minimum price bound")
    max_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Maximum price bound")
    size: Optional[str] = Field(default=None, max_length=50, description="Garment/shoe size filter")
    color: Optional[str] = Field(default=None, max_length=50, description="Color filter")
    in_stock: Optional[bool] = Field(default=None, description="Filter by stock availability")
    sort: Optional[SearchSort] = Field(default=None, description="Sorting criteria")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=50, description="Items per page (max 50)")


# ==============================================================================
# Filter Metadata Schemas
# ==============================================================================

class FilterCategoryOption(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class FilterBrandOption(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class SearchFilterOptionsResponse(BaseModel):
    """Available discovery facets and bounds for active marketplace listings."""

    categories: List[FilterCategoryOption] = []
    brands: List[FilterBrandOption] = []
    sizes: List[str] = []
    colors: List[str] = []
    min_price: Decimal = Decimal("0.00")
    max_price: Decimal = Decimal("0.00")


# ==============================================================================
# Public Search Result Item Schemas
# ==============================================================================

class SearchProductVariantItem(BaseModel):
    """Public SKU variant representation without internal inventory quantities."""

    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    is_active: bool = True
    is_in_stock: bool = False

    model_config = ConfigDict(from_attributes=True)


class SearchProductMediaItem(BaseModel):
    """Public media asset item."""

    id: uuid.UUID
    url: str
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False

    model_config = ConfigDict(from_attributes=True)


class SearchProductBrandItem(BaseModel):
    """Public brand snippet."""

    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class SearchProductCategoryItem(BaseModel):
    """Public category snippet."""

    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class SearchProductItem(BaseModel):
    """Public product search result item with public-only attributes."""

    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    base_price: Decimal
    currency: str = "USD"
    status: ProductStatus = ProductStatus.ACTIVE
    is_active: bool = True
    brand: Optional[SearchProductBrandItem] = None
    category: Optional[SearchProductCategoryItem] = None
    variants: List[SearchProductVariantItem] = []
    media: List[SearchProductMediaItem] = []
    is_in_stock: bool = False

    model_config = ConfigDict(from_attributes=True)


class SearchProductsResponse(BaseModel):
    """Paginated search response envelope."""

    items: List[SearchProductItem]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
