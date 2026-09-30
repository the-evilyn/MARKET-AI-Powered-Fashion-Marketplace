from enum import Enum


class PaymentStatus(str, Enum):
    """Lifecycle status for order payments."""
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentProvider(str, Enum):
    """Supported payment gateway providers."""
    PAYPAL = "PAYPAL"
