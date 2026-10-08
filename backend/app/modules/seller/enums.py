from enum import Enum


class StoreStatus(str, Enum):
    """Lifecycle and operational status of a seller storefront."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"
