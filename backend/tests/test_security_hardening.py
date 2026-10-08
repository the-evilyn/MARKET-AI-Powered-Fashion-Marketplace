from decimal import Decimal
import logging
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient, Response
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.payments.providers.paypal import PayPalClient
from app.modules.payments.routes import payment_service
from app.modules.users.enums import UserRole
from tests.test_cart import create_catalog_item
from tests.test_payments import setup_customer_with_order


# ==============================================================================
# 1. JWT Secret Safety Tests
# ==============================================================================

@pytest.mark.parametrize(
    "insecure_secret",
    [
        "super_secret_jwt_signing_key_replace_in_production_min32chars",
        "secret",
        "changeme",
        "jwt_secret",
        "your_jwt_secret",
        "replace_in_production",
        "password",
        "12345678",
        "secret123",
        "admin",
    ],
)
def test_jwt_insecure_defaults_rejected_in_production(insecure_secret: str):
    """Production startup must strictly reject all known insecure default JWT secrets."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="production", JWT_SECRET=insecure_secret)
    err_msg = str(exc_info.value)
    assert (
        "Insecure default JWT signing key detected" in err_msg
        or "JWT signing key must be at least 32 characters long" in err_msg
    )
    # Ensure secret value is never printed (for non-dictionary words)
    assert insecure_secret not in err_msg


@pytest.mark.parametrize(
    "insecure_secret",
    [
        "super_secret_jwt_signing_key_replace_in_production_min32chars",
        "secret",
        "changeme",
        "jwt_secret",
        "your_jwt_secret",
        "replace_in_production",
        "password",
        "12345678",
        "secret123",
        "admin",
    ],
)
def test_jwt_insecure_defaults_rejected_in_staging(insecure_secret: str):
    """Staging startup must strictly reject all known insecure default JWT secrets."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="staging", JWT_SECRET=insecure_secret)
    err_msg = str(exc_info.value)
    assert (
        "Insecure default JWT signing key detected" in err_msg
        or "JWT signing key must be at least 32 characters long" in err_msg
    )
    assert insecure_secret not in err_msg


def test_jwt_secret_empty_or_whitespace_rejected():
    """Empty or whitespace-only JWT secret must be rejected in any environment."""
    for env in ["development", "test", "staging", "production"]:
        with pytest.raises(ValidationError) as exc_info:
            Settings(APP_ENV=env, JWT_SECRET="   ")
        assert "JWT signing key must not be empty" in str(exc_info.value)


def test_jwt_secret_production_length_requirement():
    """Production requires a secret of at least 32 characters."""
    short_secret = "a" * 31
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="production", JWT_SECRET=short_secret)
    err_msg = str(exc_info.value)
    assert "JWT signing key must be at least 32 characters long" in err_msg
    assert short_secret not in err_msg

    # Exactly 32 characters of random strong key succeeds
    valid_32_secret = "k" * 32
    settings = Settings(APP_ENV="production", JWT_SECRET=valid_32_secret)
    assert settings.JWT_SECRET == valid_32_secret


def test_jwt_secret_dev_convenience_preserved():
    """Local development and test environments allow default secret for developer convenience."""
    dev_settings = Settings(APP_ENV="development")
    assert dev_settings.JWT_SECRET == "super_secret_jwt_signing_key_replace_in_production_min32chars"

    test_settings = Settings(APP_ENV="test")
    assert test_settings.JWT_SECRET == "super_secret_jwt_signing_key_replace_in_production_min32chars"


# ==============================================================================
# 2. PayPal Webhook Verification Unit Tests (PayPalClient)
# ==============================================================================

@pytest.mark.asyncio
async def test_paypal_webhook_rejected_in_production_when_webhook_id_missing():
    """Production client must never accept a webhook when PAYPAL_WEBHOOK_ID is missing."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET="x" * 40,
        PAYPAL_CLIENT_ID="mock_client_id",
        PAYPAL_CLIENT_SECRET="mock_client_secret",
        PAYPAL_WEBHOOK_ID=None,
    )
    client = PayPalClient(settings=prod_settings)
    assert not client.webhook_id
    assert client.is_configured()

    verified = await client.verify_webhook_signature(
        headers={"paypal-transmission-id": "123"},
        body_json={"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    )
    assert verified is False


@pytest.mark.asyncio
async def test_paypal_webhook_rejected_in_production_when_credentials_missing():
    """Production client must reject webhook when PayPal client credentials are missing."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET="x" * 40,
        PAYPAL_CLIENT_ID=None,
        PAYPAL_CLIENT_SECRET=None,
        PAYPAL_WEBHOOK_ID="WH-PROD-12345",
    )
    client = PayPalClient(settings=prod_settings)
    assert client.webhook_id
    assert not client.is_configured()

    verified = await client.verify_webhook_signature(
        headers={
            "paypal-transmission-id": "tx-1",
            "paypal-transmission-time": "2026-10-08T10:00:00Z",
            "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-transmission-sig": "signature==",
        },
        body_json={"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    )
    assert verified is False


@pytest.mark.asyncio
async def test_paypal_webhook_rejected_in_staging_when_webhook_id_missing():
    """Staging client must strictly reject webhooks when PAYPAL_WEBHOOK_ID is missing."""
    staging_settings = Settings(
        APP_ENV="staging",
        JWT_SECRET="x" * 40,
        PAYPAL_CLIENT_ID="mock_client_id",
        PAYPAL_CLIENT_SECRET="mock_client_secret",
        PAYPAL_WEBHOOK_ID=None,
    )
    client = PayPalClient(settings=staging_settings)
    assert not client.webhook_id
    assert client.is_configured()

    verified = await client.verify_webhook_signature(
        headers={"paypal-transmission-id": "123"},
        body_json={"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    )
    assert verified is False


@pytest.mark.asyncio
async def test_paypal_webhook_rejected_in_staging_when_credentials_missing():
    """Staging client must reject webhooks when PayPal client credentials are missing."""
    staging_settings = Settings(
        APP_ENV="staging",
        JWT_SECRET="x" * 40,
        PAYPAL_CLIENT_ID=None,
        PAYPAL_CLIENT_SECRET=None,
        PAYPAL_WEBHOOK_ID="WH-STAGING-12345",
    )
    client = PayPalClient(settings=staging_settings)
    assert client.webhook_id
    assert not client.is_configured()

    verified = await client.verify_webhook_signature(
        headers={
            "paypal-transmission-id": "tx-1",
            "paypal-transmission-time": "2026-10-08T10:00:00Z",
            "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-transmission-sig": "signature==",
        },
        body_json={"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    )
    assert verified is False


@pytest.mark.asyncio
async def test_paypal_webhook_rejected_when_transmission_headers_missing():
    """Webhook verification must reject requests missing any of the 5 required transmission headers."""
    settings = Settings(
        APP_ENV="development",
        PAYPAL_CLIENT_ID="mock_id",
        PAYPAL_CLIENT_SECRET="mock_secret",
        PAYPAL_WEBHOOK_ID="WH-TEST-123",
    )
    client = PayPalClient(settings=settings)

    incomplete_headers = {
        "paypal-transmission-id": "tx-1",
        "paypal-transmission-time": "2026-10-08T10:00:00Z",
        # Missing cert-url, auth-algo, transmission-sig
    }

    verified = await client.verify_webhook_signature(
        headers=incomplete_headers,
        body_json={"event_type": "PAYMENT.CAPTURE.COMPLETED"},
    )
    assert verified is False


@pytest.mark.asyncio
async def test_paypal_webhook_client_verification_status_handling():
    """Unit test PayPalClient verifying signature against PayPal API."""
    settings = Settings(
        APP_ENV="development",
        PAYPAL_CLIENT_ID="mock_id",
        PAYPAL_CLIENT_SECRET="mock_secret",
        PAYPAL_WEBHOOK_ID="WH-TEST-123",
    )
    client = PayPalClient(settings=settings)

    headers = {
        "paypal-transmission-id": "tx-test-unit",
        "paypal-transmission-time": "2026-10-08T10:00:00Z",
        "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-transmission-sig": "valid_sig",
    }
    payload = {"id": "WH-UNIT", "event_type": "PAYMENT.CAPTURE.COMPLETED"}

    # Mock success from PayPal
    with patch.object(client, "get_access_token", new=AsyncMock(return_value="mock_token")), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=Response(200, json={"verification_status": "SUCCESS"}))):
        assert await client.verify_webhook_signature(headers, payload) is True

    # Mock failure from PayPal
    with patch.object(client, "get_access_token", new=AsyncMock(return_value="mock_token")), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=Response(200, json={"verification_status": "FAILURE"}))):
        assert await client.verify_webhook_signature(headers, payload) is False


# ==============================================================================
# 3. Webhook Endpoint Integration & Idempotency Security Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_paypal_webhook_endpoint_rejects_unverified_in_production(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """POST /payments/paypal/webhook strictly rejects unverified webhook in production environment."""
    seller = await create_user_helper(email="seller_sec1@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_sec1@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="SEC-01", stock_qty=10, buy_qty=2
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-SEC1", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    # Simulate production environment without PAYPAL_WEBHOOK_ID configured
    with patch.object(payment_service.paypal_client.settings, "APP_ENV", "production"), \
         patch.object(payment_service.paypal_client, "webhook_id", None):

        webhook_payload = {
            "id": "WH-EVT-SEC1",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "CAP-WH-SEC1",
                "custom_id": order["id"],
                "status": "COMPLETED",
                "amount": {"value": order["total"], "currency_code": "USD"},
            },
        }

        # Attempting webhook post with unconfigured production must return 400
        res = await async_client.post(
            "/api/v1/payments/paypal/webhook",
            json=webhook_payload,
        )
        assert res.status_code == 400
        assert "PayPal webhook signature verification failed" in res.json()["detail"]

    # Crucial security check: Order and payment state must be untouched!
    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "PENDING_PAYMENT"
    assert order_check.json()["payment_status"] == "PENDING"

    # Inventory must remain reserved, NOT finalized!
    inv = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv.json()["quantity_on_hand"] == 10
    assert inv.json()["quantity_reserved"] == 2
    assert inv.json()["quantity_available"] == 8


@pytest.mark.asyncio
async def test_paypal_webhook_endpoint_rejects_unverified_in_staging(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """POST /payments/paypal/webhook strictly rejects unverified webhook in staging environment."""
    seller = await create_user_helper(email="seller_sec1_stg@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_sec1_stg@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="SEC-01-STG", stock_qty=10, buy_qty=2
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-STG1", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    # Simulate staging environment without PAYPAL_WEBHOOK_ID configured
    with patch.object(payment_service.paypal_client.settings, "APP_ENV", "staging"), \
         patch.object(payment_service.paypal_client, "webhook_id", None):

        webhook_payload = {
            "id": "WH-EVT-STG1",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "CAP-WH-STG1",
                "custom_id": order["id"],
                "status": "COMPLETED",
                "amount": {"value": order["total"], "currency_code": "USD"},
            },
        }

        # Attempting webhook post in staging without webhook ID must return 400
        res = await async_client.post(
            "/api/v1/payments/paypal/webhook",
            json=webhook_payload,
        )
        assert res.status_code == 400
        assert "PayPal webhook signature verification failed" in res.json()["detail"]

    # Order and payment state must be untouched
    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "PENDING_PAYMENT"
    assert order_check.json()["payment_status"] == "PENDING"


@pytest.mark.asyncio
async def test_paypal_webhook_invalid_signature_rejected_without_state_change(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """When signature verification fails, webhook is rejected with 400 and state remains unchanged."""
    seller = await create_user_helper(email="seller_sec2@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_sec2@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="SEC-02", stock_qty=5, buy_qty=1
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-SEC2", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    # Force signature verification failure
    with patch.object(payment_service.paypal_client, "verify_webhook_signature", new=AsyncMock(return_value=False)):
        headers = {
            "paypal-transmission-id": "tx-invalid-sig",
            "paypal-transmission-time": "2026-10-08T10:00:00Z",
            "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-transmission-sig": "tampered_signature_value",
        }
        payload = {
            "id": "WH-EVT-SEC2",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "CAP-WH-SEC2",
                "custom_id": order["id"],
                "status": "COMPLETED",
                "amount": {"value": order["total"], "currency_code": "USD"},
            },
        }

        res = await async_client.post(
            "/api/v1/payments/paypal/webhook",
            json=payload,
            headers=headers,
        )
        assert res.status_code == 400
        assert "PayPal webhook signature verification failed" in res.json()["detail"]

    # State must remain PENDING_PAYMENT
    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "PENDING_PAYMENT"
    assert order_check.json()["payment_status"] == "PENDING"

    inv = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv.json()["quantity_on_hand"] == 5
    assert inv.json()["quantity_reserved"] == 1
    assert inv.json()["quantity_available"] == 4


@pytest.mark.asyncio
async def test_paypal_webhook_verified_signature_succeeds_and_confirms_order(
    async_client: AsyncClient, create_user_helper, auth_headers_helper
):
    """When signature verification succeeds, webhook transitions order to CONFIRMED and handles idempotency."""
    seller = await create_user_helper(email="seller_sec3@example.com", role=UserRole.SELLER)
    customer = await create_user_helper(email="cust_sec3@example.com", role=UserRole.CUSTOMER)
    s_headers = auth_headers_helper(seller)
    c_headers = auth_headers_helper(customer)

    order, variant_id = await setup_customer_with_order(
        async_client, s_headers, c_headers, sku="SEC-03", stock_qty=10, buy_qty=3
    )

    with patch.object(
        payment_service.paypal_client,
        "create_order",
        new=AsyncMock(return_value={"id": "PAYPAL-ORDER-SEC3", "status": "CREATED"}),
    ):
        await async_client.post(
            "/api/v1/payments/paypal/create-order",
            json={"order_id": order["id"]},
            headers=c_headers,
        )

    headers = {
        "paypal-transmission-id": "tx-valid-sig-03",
        "paypal-transmission-time": "2026-10-08T10:00:00Z",
        "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-transmission-sig": "valid_signature_token",
    }
    payload = {
        "id": "WH-EVT-SEC3",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAP-WH-SEC3",
            "custom_id": order["id"],
            "status": "COMPLETED",
            "amount": {"value": order["total"], "currency_code": "USD"},
        },
    }

    with patch.object(payment_service.paypal_client, "verify_webhook_signature", new=AsyncMock(return_value=True)):
        # Delivery 1: Verified and processed
        res1 = await async_client.post(
            "/api/v1/payments/paypal/webhook",
            json=payload,
            headers=headers,
        )
        assert res1.status_code == 200
        assert res1.json()["status"] == "success"

        # Delivery 2 (Duplicate): Verified signature, recognized as duplicate -> ignored
        res2 = await async_client.post(
            "/api/v1/payments/paypal/webhook",
            json=payload,
            headers=headers,
        )
        assert res2.status_code == 200
        assert res2.json()["status"] == "ignored"

    # Order confirmed and stock finalized (10 - 3 = 7)
    order_check = await async_client.get(f"/api/v1/orders/{order['id']}", headers=c_headers)
    assert order_check.json()["status"] == "CONFIRMED"
    assert order_check.json()["payment_status"] == "COMPLETED"

    inv = await async_client.get(f"/api/v1/inventory/{variant_id}", headers=s_headers)
    assert inv.json()["quantity_on_hand"] == 7
    assert inv.json()["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_paypal_webhook_sanitized_logging_does_not_leak_secrets(caplog):
    """Ensure verification error logging never outputs signature values, cert URLs, or secrets."""
    caplog.set_level(logging.DEBUG)

    sensitive_sig = "SUPER_SECRET_SIGNATURE_BYTES_NEVER_LOG"
    sensitive_cert = "https://sensitive.paypal.cert.url/secret"
    headers = {
        "paypal-transmission-id": "tx-log-test",
        "paypal-transmission-time": "2026-10-08T10:00:00Z",
        "paypal-cert-url": sensitive_cert,
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-transmission-sig": sensitive_sig,
    }

    client = PayPalClient(
        settings=Settings(
            APP_ENV="development",
            PAYPAL_CLIENT_ID="id",
            PAYPAL_CLIENT_SECRET="secret",
            PAYPAL_WEBHOOK_ID="WH-LOG-TEST",
        )
    )

    with patch.object(client, "get_access_token", new=AsyncMock(return_value="mock_token")), \
         patch("httpx.AsyncClient.post", side_effect=Exception("Simulated network timeout")):

        verified = await client.verify_webhook_signature(
            headers=headers,
            body_json={"event_type": "TEST"},
        )
        assert verified is False

    # Check logs for leaks
    all_logs = " ".join([record.message for record in caplog.records])
    assert sensitive_sig not in all_logs
    assert sensitive_cert not in all_logs
