from enum import Enum


class ProductStatus(str, Enum):
    """Lifecycle status for marketplace products."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MediaType(str, Enum):
    """Supported media asset formats for product showcases."""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    LOOKBOOK = "LOOKBOOK"
