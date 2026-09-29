import uuid
from datetime import timedelta
import pytest
from httpx import AsyncClient

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.dependencies import require_roles
from app.modules.users.enums import UserRole
from app.modules.users.models import User


# ==============================================================================
# Security & Hashing Tests
# ==============================================================================

def test_password_hashing_behavior():
    """Verify that Argon2id generates salted, irreversible, verifiable hashes."""
    raw_password = "SuperSecretPassword123!"
    hash1 = hash_password(raw_password)
    hash2 = hash_password(raw_password)

    # Hashes must differ because of distinct random salts
    assert hash1 != hash2
    assert hash1 != raw_password

    # Correct password verification
    assert verify_password(raw_password, hash1) is True
    assert verify_password(raw_password, hash2) is True

    # Wrong password verification
    assert verify_password("WrongPassword123!", hash1) is False
    assert verify_password("", hash1) is False
    assert verify_password(raw_password, "invalid_corrupted_hash") is False


def test_jwt_creation_and_validation():
    """Verify that JWT creation encodes claims and decoding validates them."""
    test_id = str(uuid.uuid4())
    claims = {"email": "jwt@example.com", "role": "SELLER"}

    token = create_access_token(subject=test_id, claims=claims)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == test_id
    assert payload["email"] == "jwt@example.com"
    assert payload["role"] == "SELLER"
    assert "exp" in payload

    # Test expired token
    expired_token = create_access_token(
        subject=test_id,
        expires_delta=timedelta(seconds=-10),
    )
    assert decode_access_token(expired_token) is None

    # Test invalid token format
    assert decode_access_token("not.a.valid.jwt.token") is None


# ==============================================================================
# Registration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_successful_registration(async_client: AsyncClient):
    """Test successful self-registration as a customer."""
    payload = {
        "email": "fashionista@example.com",
        "password": "Password1234!",
        "first_name": "Coco",
        "last_name": "Chanel",
        "role": "CUSTOMER",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "fashionista@example.com"
    assert data["user"]["first_name"] == "Coco"
    assert data["user"]["last_name"] == "Chanel"
    assert data["user"]["role"] == "CUSTOMER"
    assert data["user"]["is_active"] is True
    assert "password_hash" not in data["user"]


@pytest.mark.asyncio
async def test_seller_registration(async_client: AsyncClient):
    """Test successful self-registration as a seller."""
    payload = {
        "email": "boutique@example.com",
        "password": "Password1234!",
        "first_name": "Guccio",
        "last_name": "Gucci",
        "role": "SELLER",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "SELLER"


@pytest.mark.asyncio
async def test_duplicate_email_registration(async_client: AsyncClient, create_user_helper):
    """Test that registering an existing email fails safely."""
    await create_user_helper(email="existing@example.com")

    payload = {
        "email": "existing@example.com",
        "password": "NewPassword123!",
        "first_name": "Jane",
        "last_name": "Doe",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_registration_data(async_client: AsyncClient):
    """Test registration validation errors for malformed emails and short passwords."""
    # Invalid email
    res1 = await async_client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Password123!",
        "first_name": "A",
        "last_name": "B",
    })
    assert res1.status_code == 422

    # Short password (< 8 chars)
    res2 = await async_client.post("/api/v1/auth/register", json={
        "email": "valid@example.com",
        "password": "short",
        "first_name": "A",
        "last_name": "B",
    })
    assert res2.status_code == 422

    # Attempt to self-register as ADMIN
    res3 = await async_client.post("/api/v1/auth/register", json={
        "email": "fakeadmin@example.com",
        "password": "Password123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "ADMIN",
    })
    assert res3.status_code == 422


# ==============================================================================
# Authentication / Login Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_successful_login(async_client: AsyncClient, create_user_helper):
    """Test login with valid credentials."""
    await create_user_helper(
        email="loginuser@example.com",
        password="MySecretPassword123!",
        first_name="Login",
        last_name="Tester",
    )

    response = await async_client.post("/api/v1/auth/login", json={
        "email": "loginuser@example.com",
        "password": "MySecretPassword123!",
    })
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, create_user_helper):
    """Test login with invalid password returns safe 401 error."""
    await create_user_helper(
        email="wrongpass@example.com",
        password="CorrectPassword123!",
    )

    response = await async_client.post("/api/v1/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "IncorrectPassword999!",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with non-existent user returns safe 401 error without leaking user presence."""
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "Password123!",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(async_client: AsyncClient, create_user_helper):
    """Test that deactivated accounts cannot log in."""
    await create_user_helper(
        email="inactive@example.com",
        password="Password123!",
        is_active=False,
    )

    response = await async_client.post("/api/v1/auth/login", json={
        "email": "inactive@example.com",
        "password": "Password123!",
    })
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Test authenticated logout endpoint."""
    user = await create_user_helper(email="logout@example.com")
    headers = auth_headers_helper(user)

    response = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()


# ==============================================================================
# User Identity Endpoint (/users/me) & Role Authorization Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_authenticated_me_endpoint(async_client: AsyncClient, create_user_helper, auth_headers_helper):
    """Test GET /api/v1/users/me returns authenticated user's details."""
    user = await create_user_helper(
        email="me@example.com",
        first_name="Jane",
        last_name="Birkin",
        role=UserRole.SELLER,
    )
    headers = auth_headers_helper(user)

    response = await async_client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == "me@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Birkin"
    assert data["role"] == "SELLER"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_unauthenticated_me_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/users/me without credentials returns 401."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(async_client: AsyncClient):
    """Test GET /api/v1/users/me with corrupted token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = await async_client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_role_authorization_dependency():
    """Verify require_roles dependency logic."""
    customer = User(
        id=uuid.uuid4(),
        email="c@example.com",
        password_hash="hash",
        first_name="Cust",
        last_name="Omer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    seller = User(
        id=uuid.uuid4(),
        email="s@example.com",
        password_hash="hash",
        first_name="Sel",
        last_name="Ler",
        role=UserRole.SELLER,
        is_active=True,
    )
    admin = User(
        id=uuid.uuid4(),
        email="a@example.com",
        password_hash="hash",
        first_name="Ad",
        last_name="Min",
        role=UserRole.ADMIN,
        is_active=True,
    )

    admin_only = require_roles(UserRole.ADMIN)
    seller_or_admin = require_roles(UserRole.SELLER, UserRole.ADMIN)

    # Admin passes admin_only
    assert await admin_only(current_user=admin) == admin

    # Seller fails admin_only
    with pytest.raises(Exception) as exc:
        await admin_only(current_user=seller)
    assert exc.value.status_code == 403

    # Customer fails seller_or_admin
    with pytest.raises(Exception) as exc:
        await seller_or_admin(current_user=customer)
    assert exc.value.status_code == 403

    # Seller passes seller_or_admin
    assert await seller_or_admin(current_user=seller) == seller
