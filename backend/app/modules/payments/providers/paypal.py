from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger("ai_fashion_marketplace.payments.paypal")


class PayPalClient:
    """Server-side client for PayPal REST APIs in Sandbox mode."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = (self.settings.PAYPAL_BASE_URL or "https://api-m.sandbox.paypal.com").rstrip("/")
        self.client_id = self.settings.PAYPAL_CLIENT_ID
        self.client_secret = self.settings.PAYPAL_CLIENT_SECRET
        self.webhook_id = self.settings.PAYPAL_WEBHOOK_ID

        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def is_configured(self) -> bool:
        """Check whether PayPal Sandbox credentials are provided."""
        return bool(self.client_id and self.client_secret)

    async def get_access_token(self) -> str:
        """
        Obtain server-side OAuth 2.0 bearer token using client_credentials grant.
        Caches token until near expiry.
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PayPal Sandbox is not configured. Please set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.",
            )

        now = datetime.now(timezone.utc)
        if self._cached_token and self._token_expires_at and now < self._token_expires_at:
            return self._cached_token

        url = f"{self.base_url}/v1/oauth2/token"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"Accept": "application/json", "Accept-Language": "en_US"},
                )
        except httpx.RequestError as exc:
            logger.error(f"PayPal network error requesting access token: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to PayPal API.",
            )

        if response.status_code != 200:
            logger.error(f"PayPal OAuth error HTTP {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PayPal authentication failed. Check your sandbox credentials.",
            )

        data = response.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PayPal did not return an access token.",
            )

        self._cached_token = token
        # Buffer expiry by 60 seconds
        self._token_expires_at = now + timedelta(seconds=max(0, expires_in - 60))
        return token

    async def create_order(
        self,
        order_id: str,
        order_number: str,
        amount: Decimal,
        currency: str = "USD",
    ) -> Dict[str, Any]:
        """
        Create a server-side PayPal order for capture.
        The DB order amount is authoritative.
        """
        token = await self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders"

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(order_id),
                    "custom_id": str(order_id),
                    "invoice_id": order_number,
                    "description": f"AI Fashion Order {order_number}",
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                }
            ],
            "application_context": {
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.RequestError as exc:
            logger.error(f"PayPal network error creating order: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach PayPal while creating payment order.",
            )

        if response.status_code not in (200, 201):
            logger.error(f"PayPal create order error {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PayPal order creation was rejected.",
            )

        return response.json()

    async def capture_order(self, paypal_order_id: str) -> Dict[str, Any]:
        """
        Capture payment for an approved PayPal order server-side.
        """
        token = await self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/capture"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.RequestError as exc:
            logger.error(f"PayPal network error capturing order {paypal_order_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network error communicating with PayPal during capture.",
            )

        if response.status_code not in (200, 201):
            logger.warning(
                f"PayPal capture rejected HTTP {response.status_code} for order {paypal_order_id}: {response.text}"
            )
            # Return JSON payload if available so service can distinguish rejection reasons
            try:
                err_data = response.json()
                return err_data
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PayPal payment capture failed or was rejected.",
                )

        return response.json()

    async def get_order_details(self, paypal_order_id: str) -> Dict[str, Any]:
        """Fetch details of an order from PayPal."""
        token = await self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{paypal_order_id}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.RequestError as exc:
            logger.error(f"PayPal network error fetching order {paypal_order_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to PayPal API.",
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PayPal order '{paypal_order_id}' not found.",
            )

        return response.json()

    async def verify_webhook_signature(
        self,
        headers: Dict[str, str],
        body_json: Dict[str, Any],
    ) -> bool:
        """
        Verify incoming webhook signature using PayPal's verification endpoint.
        Rejects unverifiable notifications safely and enforces strict verification in production.
        """
        is_strict_env = (self.settings.APP_ENV or "").strip().lower() in ("production", "prod", "staging")

        # In production and staging, PAYPAL_WEBHOOK_ID and API credentials are strictly required
        if is_strict_env:
            if not self.webhook_id:
                logger.error("PayPal webhook verification failed: PAYPAL_WEBHOOK_ID is not configured in production/staging.")
                return False
            if not self.is_configured():
                logger.error("PayPal webhook verification failed: PayPal client credentials are not configured in production/staging.")
                return False
        else:
            # In development/test mode without webhook ID, bypass verification for convenience
            if not self.webhook_id:
                logger.info("PAYPAL_WEBHOOK_ID not set; skipping webhook signature verification in non-production environment.")
                return True

            # If webhook_id is provided in dev/test, credentials are required
            if not self.is_configured():
                logger.warning("PayPal webhook verification failed: PayPal credentials missing while PAYPAL_WEBHOOK_ID is configured.")
                return False

        # PayPal transmission headers are case-insensitive
        lower_headers = {k.lower(): str(v) for k, v in headers.items()}
        transmission_id = lower_headers.get("paypal-transmission-id")
        transmission_time = lower_headers.get("paypal-transmission-time")
        cert_url = lower_headers.get("paypal-cert-url")
        auth_algo = lower_headers.get("paypal-auth-algo")
        transmission_sig = lower_headers.get("paypal-transmission-sig")

        # Reject notifications missing required signature headers
        if not all([transmission_id, transmission_time, cert_url, auth_algo, transmission_sig]):
            logger.warning("PayPal webhook verification rejected: Missing required transmission signature headers.")
            return False

        try:
            token = await self.get_access_token()
        except HTTPException:
            logger.error("Failed to obtain PayPal access token for webhook signature verification.")
            return False

        url = f"{self.base_url}/v1/notifications/verify-webhook-signature"
        payload = {
            "transmission_id": transmission_id,
            "transmission_time": transmission_time,
            "cert_url": cert_url,
            "auth_algo": auth_algo,
            "transmission_sig": transmission_sig,
            "webhook_id": self.webhook_id,
            "webhook_event": body_json,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
            if res.status_code == 200:
                data = res.json()
                return data.get("verification_status") == "SUCCESS"

            logger.warning(f"PayPal webhook signature verification returned status code {res.status_code}.")
            return False
        except httpx.RequestError as exc:
            logger.error(f"Network error during PayPal webhook verification: {exc.__class__.__name__}")
            return False
        except Exception:
            logger.error("Unexpected error during PayPal webhook signature verification.")
            return False
