from enum import Enum


class CartStatus(str, Enum):
    """Lifecycle status for a shopping cart."""
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"
