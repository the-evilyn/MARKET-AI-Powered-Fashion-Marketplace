from datetime import datetime, timezone
from decimal import Decimal
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inventory.service import InventoryService
from app.modules.orders.enums import OrderStatus
from app.modules.orders.models import Order, SubOrder
from app.modules.payments.enums import PaymentProvider, PaymentStatus
from app.modules.payments.models import Payment, PaymentWebhookEvent
from app.modules.payments.providers.paypal import PayPalClient
from app.modules.payments.schemas import (
    PayPalCancelResponse,
    PayPalCaptureResponse,
    PayPalCreateOrderResponse,
)

logger = logging.getLogger("ai_fashion_marketplace.payments.service")


class PaymentService:
    """Orchestrates payments, order state transitions, and inventory finalization/release."""

    def __init__(self, paypal_client: Optional[PayPalClient] = None):
        self.paypal_client = paypal_client or PayPalClient()

    async def create_paypal_order(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> PayPalCreateOrderResponse:
        """
        Create a server-side PayPal checkout order for an internal PENDING_PAYMENT order.
        Amount and currency are strictly derived from the DB order record.
        """
        # 1. Fetch internal order
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.payment))
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order '{order_id}' not found.",
            )

        # 2. Enforce customer ownership (IDOR protection)
        if order.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to pay for this order.",
            )

        # 3. Verify order status
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot initiate payment for order with status '{order.status.value}'.",
            )

        # 4. Check existing payment record
        if order.payment:
            if order.payment.status == PaymentStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This order has already been paid and completed.",
                )

        # 5. Call PayPal REST API using authoritative DB total
        paypal_data = await self.paypal_client.create_order(
            order_id=str(order.id),
            order_number=order.order_number,
            amount=order.total,
            currency=order.currency,
        )
        paypal_order_id = paypal_data.get("id")
        if not paypal_order_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PayPal did not return an order ID.",
            )

        # 6. Upsert Payment entity
        now = datetime.now(timezone.utc)
        if order.payment:
            payment = order.payment
            payment.provider = PaymentProvider.PAYPAL
            payment.provider_order_id = paypal_order_id
            payment.status = PaymentStatus.PENDING
            payment.amount = order.total
            payment.currency = order.currency
            payment.updated_at = now
        else:
            payment = Payment(
                id=uuid.uuid4(),
                order_id=order.id,
                provider=PaymentProvider.PAYPAL,
                provider_order_id=paypal_order_id,
                status=PaymentStatus.PENDING,
                amount=order.total,
                currency=order.currency,
                created_at=now,
                updated_at=now,
            )
            db.add(payment)

        await db.commit()
        await db.refresh(payment)

        return PayPalCreateOrderResponse(
            payment_id=payment.id,
            paypal_order_id=paypal_order_id,
            amount=order.total,
            currency=order.currency,
            provider=PaymentProvider.PAYPAL.value,
        )

    @staticmethod
    async def _sync_sub_orders_status(
        db: AsyncSession,
        order_id: uuid.UUID,
        target_status: OrderStatus,
        timestamp: datetime,
    ) -> None:
        """Keep vendor sub-orders in sync with parent order payment transitions."""
        stmt = select(SubOrder).where(SubOrder.order_id == order_id)
        res = await db.execute(stmt)
        for so in res.scalars().all():
            so.status = target_status
            so.updated_at = timestamp

    async def capture_paypal_payment(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        paypal_order_id: str,
    ) -> PayPalCaptureResponse:
        """
        Capture payment for an approved PayPal order.
        Verifies customer ownership, validates amount, finalizes inventory reservation,
        and transitions Order -> CONFIRMED, Payment -> COMPLETED in one atomic transaction.
        """
        # 1. Fetch Payment by provider_order_id
        stmt = (
            select(Payment)
            .where(Payment.provider_order_id == paypal_order_id)
            .options(selectinload(Payment.order))
        )
        res = await db.execute(stmt)
        payment = res.scalar_one_or_none()

        if not payment or not payment.order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment for PayPal order '{paypal_order_id}' not found.",
            )

        order = payment.order

        # 2. Enforce customer ownership (Customer A cannot capture Customer B payment)
        if order.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to capture this payment.",
            )

        # 3. Idempotency check: if already confirmed and completed, return current state
        if order.status == OrderStatus.CONFIRMED and payment.status == PaymentStatus.COMPLETED:
            return PayPalCaptureResponse(
                payment_id=payment.id,
                order_id=order.id,
                order_number=order.order_number,
                status=payment.status,
                order_status=order.status,
                provider_order_id=payment.provider_order_id or paypal_order_id,
                provider_payment_id=payment.provider_payment_id,
                amount=payment.amount,
                currency=payment.currency,
            )

        if order.status != OrderStatus.PENDING_PAYMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be captured in status '{order.status.value}'.",
            )

        # 4. Execute server-side capture with PayPal
        capture_data = await self.paypal_client.capture_order(paypal_order_id)
        paypal_status = capture_data.get("status")

        now = datetime.now(timezone.utc)

        if paypal_status == "COMPLETED":
            # Extract capture details
            captures = (
                capture_data.get("purchase_units", [{}])[0]
                .get("payments", {})
                .get("captures", [])
            )
            capture_item = captures[0] if captures else {}
            provider_payment_id = capture_item.get("id")

            # Price security: verify captured amount matches internal order total
            val_str = capture_item.get("amount", {}).get("value")
            cur_code = capture_item.get("amount", {}).get("currency_code")
            if val_str:
                captured_val = Decimal(val_str)
                if captured_val != order.total or (cur_code and cur_code != order.currency):
                    logger.error(
                        f"CRITICAL: Amount mismatch during capture for order {order.id}! "
                        f"Expected {order.total} {order.currency}, PayPal gave {captured_val} {cur_code}"
                    )
                    # Reject payment, cancel order, release reservation
                    payment.status = PaymentStatus.FAILED
                    payment.updated_at = now
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = now
                    await InventoryService.release_order_inventory(db, order.id)
                    await db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Payment verification failed: captured amount does not match order total.",
                    )

            # Payment SUCCESS: transition states and finalize stock reservation
            payment.status = PaymentStatus.COMPLETED
            payment.provider_payment_id = provider_payment_id
            payment.updated_at = now

            order.status = OrderStatus.CONFIRMED
            order.updated_at = now
            await self._sync_sub_orders_status(db, order.id, OrderStatus.CONFIRMED, now)

            # Atomically finalize inventory (decrements reserved and on_hand)
            await InventoryService.finalize_order_inventory(db, order.id)

            await db.commit()
            await db.refresh(payment)
            await db.refresh(order)

            return PayPalCaptureResponse(
                payment_id=payment.id,
                order_id=order.id,
                order_number=order.order_number,
                status=payment.status,
                order_status=order.status,
                provider_order_id=payment.provider_order_id or paypal_order_id,
                provider_payment_id=payment.provider_payment_id,
                amount=payment.amount,
                currency=payment.currency,
            )
        else:
            # Payment DENIED / FAILED by PayPal
            logger.warning(
                f"PayPal payment capture failed with status '{paypal_status}' for order {order.id}"
            )
            payment.status = PaymentStatus.FAILED
            payment.updated_at = now

            order.status = OrderStatus.CANCELLED
            order.updated_at = now
            await self._sync_sub_orders_status(db, order.id, OrderStatus.CANCELLED, now)

            # Release reserved inventory back to available
            await InventoryService.release_order_inventory(db, order.id)

            await db.commit()
            await db.refresh(payment)
            await db.refresh(order)

            return PayPalCaptureResponse(
                payment_id=payment.id,
                order_id=order.id,
                order_number=order.order_number,
                status=payment.status,
                order_status=order.status,
                provider_order_id=payment.provider_order_id or paypal_order_id,
                provider_payment_id=payment.provider_payment_id,
                amount=payment.amount,
                currency=payment.currency,
            )

    async def cancel_paypal_payment(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        paypal_order_id: str,
    ) -> PayPalCancelResponse:
        """
        Handle customer cancellation or abandonment of a PayPal payment.
        Transitions Payment -> CANCELLED, Order -> CANCELLED, and releases inventory reservation.
        """
        stmt = (
            select(Payment)
            .where(Payment.provider_order_id == paypal_order_id)
            .options(selectinload(Payment.order))
        )
        res = await db.execute(stmt)
        payment = res.scalar_one_or_none()

        if not payment or not payment.order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment for PayPal order '{paypal_order_id}' not found.",
            )

        order = payment.order

        # Ownership check
        if order.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel this payment.",
            )

        # Idempotent return if already cancelled
        if order.status == OrderStatus.CANCELLED and payment.status == PaymentStatus.CANCELLED:
            return PayPalCancelResponse(
                payment_id=payment.id,
                order_id=order.id,
                order_number=order.order_number,
                status=payment.status,
                order_status=order.status,
            )

        if order.status == OrderStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel payment for an already confirmed order.",
            )

        now = datetime.now(timezone.utc)
        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = now

        order.status = OrderStatus.CANCELLED
        order.updated_at = now
        await self._sync_sub_orders_status(db, order.id, OrderStatus.CANCELLED, now)

        # Release inventory reservation
        await InventoryService.release_order_inventory(db, order.id)

        await db.commit()
        await db.refresh(payment)
        await db.refresh(order)

        return PayPalCancelResponse(
            payment_id=payment.id,
            order_id=order.id,
            order_number=order.order_number,
            status=payment.status,
            order_status=order.status,
        )

    async def process_webhook(
        self,
        db: AsyncSession,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Idempotent PayPal webhook handler.
        Safely processes PAYMENT.CAPTURE.COMPLETED, PAYMENT.CAPTURE.DENIED,
        PAYMENT.CAPTURE.PENDING, and CHECKOUT.PAYMENT-APPROVAL.REVERSED.
        """
        event_id = payload.get("id")
        event_type = payload.get("event_type")

        if not event_id or not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required webhook event identifiers.",
            )

        # 1. Idempotency check: ignore already processed webhook events
        stmt = select(PaymentWebhookEvent).where(
            PaymentWebhookEvent.provider == "PAYPAL",
            PaymentWebhookEvent.event_id == event_id,
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            logger.info(f"Webhook event '{event_id}' already processed. Idempotent no-op.")
            return {"status": "ignored", "detail": "Event already processed"}

        # 2. Cryptographic signature check if webhook verification is configured
        verified = await self.paypal_client.verify_webhook_signature(headers, payload)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PayPal webhook signature verification failed.",
            )

        # 3. Process event resource
        resource = payload.get("resource", {})
        now = datetime.now(timezone.utc)

        # Determine target payment by custom_id (order_id) or PayPal IDs
        custom_id = resource.get("custom_id")
        paypal_order_id = (
            resource.get("supplementary_data", {})
            .get("related_ids", {})
            .get("order_id")
        )
        capture_id = resource.get("id")

        payment = None
        if custom_id:
            try:
                order_uuid = uuid.UUID(custom_id)
                stmt = (
                    select(Payment)
                    .where(Payment.order_id == order_uuid)
                    .options(selectinload(Payment.order))
                )
                res = await db.execute(stmt)
                payment = res.scalar_one_or_none()
            except ValueError:
                pass

        if not payment and paypal_order_id:
            stmt = (
                select(Payment)
                .where(Payment.provider_order_id == paypal_order_id)
                .options(selectinload(Payment.order))
            )
            res = await db.execute(stmt)
            payment = res.scalar_one_or_none()

        if not payment and capture_id:
            stmt = (
                select(Payment)
                .where(Payment.provider_payment_id == capture_id)
                .options(selectinload(Payment.order))
            )
            res = await db.execute(stmt)
            payment = res.scalar_one_or_none()

        # Handle specific event types
        if payment and payment.order:
            order = payment.order
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                if order.status == OrderStatus.PENDING_PAYMENT:
                    payment.status = PaymentStatus.COMPLETED
                    if capture_id:
                        payment.provider_payment_id = capture_id
                    payment.updated_at = now
                    order.status = OrderStatus.CONFIRMED
                    order.updated_at = now
                    await self._sync_sub_orders_status(db, order.id, OrderStatus.CONFIRMED, now)
                    await InventoryService.finalize_order_inventory(db, order.id)

            elif event_type in ("PAYMENT.CAPTURE.DENIED", "CHECKOUT.PAYMENT-APPROVAL.REVERSED"):
                if order.status == OrderStatus.PENDING_PAYMENT:
                    payment.status = (
                        PaymentStatus.FAILED
                        if event_type == "PAYMENT.CAPTURE.DENIED"
                        else PaymentStatus.CANCELLED
                    )
                    payment.updated_at = now
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = now
                    await self._sync_sub_orders_status(db, order.id, OrderStatus.CANCELLED, now)
                    await InventoryService.release_order_inventory(db, order.id)

            elif event_type == "PAYMENT.CAPTURE.PENDING":
                if payment.status == PaymentStatus.PENDING:
                    payment.status = PaymentStatus.AUTHORIZED
                    payment.updated_at = now

        # 4. Record webhook event for future idempotency
        webhook_log = PaymentWebhookEvent(
            id=uuid.uuid4(),
            provider="PAYPAL",
            event_id=event_id,
            event_type=event_type,
            processed_at=now,
        )
        db.add(webhook_log)

        await db.commit()
        return {"status": "success", "detail": f"Processed {event_type}"}
