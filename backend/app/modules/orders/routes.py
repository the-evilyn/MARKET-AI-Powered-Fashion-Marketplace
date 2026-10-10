import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.orders.enums import OrderStatus
from app.modules.orders.schemas import OrderResponse
from app.modules.orders.service import CheckoutService, OrderService
from app.modules.users.enums import UserRole
from app.modules.users.models import User


router = APIRouter(tags=["Orders & Checkout"])


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout active cart and create order",
)
async def checkout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> OrderResponse:
    """
    Execute atomic checkout of the customer's active cart.
    Validates product availability and stock under row-level lock, applies authoritative prices,
    creates the Order with historical snapshots, decrements inventory, and marks cart as CHECKED_OUT.
    Order starts in PENDING_PAYMENT status.
    """
    order = await CheckoutService.checkout(db, current_user.id)
    return OrderResponse.model_validate(order)


@router.get("/orders", response_model=List[OrderResponse], summary="List customer orders")
async def list_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> List[OrderResponse]:
    """Retrieve paginated order history for the authenticated customer."""
    orders = await OrderService.list_customer_orders(db, current_user.id, skip=skip, limit=limit)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderResponse, summary="Get customer order detail")
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER, UserRole.ADMIN)),
) -> OrderResponse:
    """Retrieve full details of an order belonging to the authenticated customer (or any order for admin)."""
    if current_user.role == UserRole.ADMIN:
        order = await OrderService.get_admin_order(db, order_id)
    else:
        order = await OrderService.get_by_id(db, order_id, current_user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id '{order_id}' not found.",
        )
    return OrderResponse.model_validate(order)


@router.get("/admin/orders", response_model=List[OrderResponse], summary="List all orders for admin")
async def list_admin_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[OrderStatus] = Query(default=None, description="Filter by order status"),
    customer_id: Optional[uuid.UUID] = Query(default=None, description="Filter by customer UUID"),
    seller_id: Optional[uuid.UUID] = Query(default=None, description="Filter by vendor UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> List[OrderResponse]:
    """Admin-only listing of all marketplace parent orders with sub-orders and tracking."""
    orders = await OrderService.list_admin_orders(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        seller_id=seller_id,
    )
    return [OrderResponse.model_validate(o) for o in orders]



@router.get("/admin/orders/{order_id}", response_model=OrderResponse, summary="Get any order detail for admin")
async def get_admin_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> OrderResponse:
    """Admin-only access to full details of any order."""
    order = await OrderService.get_admin_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id '{order_id}' not found.",
        )
    return OrderResponse.model_validate(order)
