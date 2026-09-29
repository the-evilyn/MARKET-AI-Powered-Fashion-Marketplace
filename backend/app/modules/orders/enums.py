from enum import Enum


class OrderStatus(str, Enum):
    """Lifecycle status for customer orders."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
