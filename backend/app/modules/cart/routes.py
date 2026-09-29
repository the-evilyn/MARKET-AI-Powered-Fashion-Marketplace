import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from app.modules.cart.service import CartService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse, summary="Get active shopping cart")
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CartResponse:
    """
    Retrieve the customer's current ACTIVE cart.
    Creates an empty active cart transactionally if none exists.
    """
    cart = await CartService.get_or_create_active_cart(db, current_user.id)
    return CartResponse.model_validate(cart)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
)
async def add_item_to_cart(
    payload: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CartResponse:
    """
    Add a purchasable SKU variant to the customer's active cart.
    If the variant already exists in the cart, increments quantity.
    Enforces product active status, variant active status, and available inventory limits.
    """
    cart = await CartService.add_item(db, current_user.id, payload)
    return CartResponse.model_validate(cart)


@router.patch("/items/{item_id}", response_model=CartResponse, summary="Update cart item quantity")
async def update_cart_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CartResponse:
    """
    Update quantity of a specific item in the customer's active cart.
    Revalidates product/variant status and available inventory.
    """
    cart = await CartService.update_item_quantity(db, current_user.id, item_id, payload.quantity)
    return CartResponse.model_validate(cart)


@router.delete("/items/{item_id}", response_model=CartResponse, summary="Remove item from cart")
async def remove_cart_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CartResponse:
    """Remove a specific item from the customer's active cart."""
    cart = await CartService.remove_item(db, current_user.id, item_id)
    return CartResponse.model_validate(cart)


@router.delete("", response_model=CartResponse, summary="Clear all items from active cart")
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CartResponse:
    """Clear all items from the customer's active cart. The cart remains ACTIVE."""
    cart = await CartService.clear_cart(db, current_user.id)
    return CartResponse.model_validate(cart)
