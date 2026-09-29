from enum import Enum


class UserRole(str, Enum):
    """System user roles for multi-vendor marketplace."""
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"
