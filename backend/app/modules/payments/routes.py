from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.payments.schemas import (
    PayPalCancelRequest,
    PayPalCancelResponse,
    PayPalCaptureRequest,
    PayPalCaptureResponse,
    PayPalCreateOrderRequest,
    PayPalCreateOrderResponse,
    WebhookProcessResponse,
)
from app.modules.payments.service import PaymentService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/payments/paypal", tags=["Payments"])

# Singleton service dependency
payment_service = PaymentService()


@router.post(
    "/create-order",
    response_model=PayPalCreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create PayPal checkout order for existing order",
)
async def create_paypal_order(
    payload: PayPalCreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> PayPalCreateOrderResponse:
    """
    Customer-only endpoint to initiate PayPal payment for an existing PENDING_PAYMENT order.
    The authoritative order amount is sourced directly from the database.
    """
    return await payment_service.create_paypal_order(
        db=db,
        customer_id=current_user.id,
        order_id=payload.order_id,
    )


@router.post(
    "/capture",
    response_model=PayPalCaptureResponse,
    status_code=status.HTTP_200_OK,
    summary="Capture approved PayPal payment and confirm order",
)
async def capture_paypal_payment(
    payload: PayPalCaptureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> PayPalCaptureResponse:
    """
    Customer-only endpoint to capture payment after buyer authorization in PayPal Sandbox.
    Enforces customer ownership, validates amount, finalizes inventory reservation,
    and updates order status to CONFIRMED.
    """
    return await payment_service.capture_paypal_payment(
        db=db,
        customer_id=current_user.id,
        paypal_order_id=payload.paypal_order_id,
    )


@router.post(
    "/cancel",
    response_model=PayPalCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel PayPal payment and release inventory reservation",
)
async def cancel_paypal_payment(
    payload: PayPalCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> PayPalCancelResponse:
    """
    Customer-only endpoint invoked when buyer cancels during PayPal checkout.
    Releases stock reservation and marks order as CANCELLED.
    """
    return await payment_service.cancel_paypal_payment(
        db=db,
        customer_id=current_user.id,
        paypal_order_id=payload.paypal_order_id,
    )


@router.post(
    "/webhook",
    response_model=WebhookProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="PayPal asynchronous event webhook",
)
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WebhookProcessResponse:
    """
    Public webhook receiver for PayPal event notifications.
    Processes captures, denials, authorizations, and reversals idempotently.
    """
    headers = dict(request.headers)
    payload: Dict[str, Any] = await request.json()
    result = await payment_service.process_webhook(
        db=db,
        headers=headers,
        payload=payload,
    )
    return WebhookProcessResponse(
        status=result["status"],
        detail=result.get("detail"),
    )
