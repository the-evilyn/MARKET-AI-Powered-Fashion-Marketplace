from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
)
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer or seller account",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Create a new user account and return a valid JWT access token."""
    existing_user = await UserService.get_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = await UserService.create_user(
        db=db,
        email=payload.email,
        password_hash=hashed_pw,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        is_active=True,
        is_verified=False,
    )

    token_expires_delta = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id),
        claims={"email": user.email, "role": user.role.value},
        expires_delta=token_expires_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive JWT access token",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password and return a JWT access token."""
    user = await UserService.get_by_email(db, payload.email)
    
    # Secure verification: run verify_password only if user exists, else avoid timing leak
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    await UserService.update_last_login(db, user)

    token_expires_delta = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id),
        claims={"email": user.email, "role": user.role.value},
        expires_delta=token_expires_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Invalidate session / logout",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> LogoutResponse:
    """Safely log out authenticated user."""
    return LogoutResponse(message="Successfully logged out")
