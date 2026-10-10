import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.admin.schemas import (
    AdminDashboardResponse,
    AdminOrderDetailResponse,
    AdminOrderListResponse,
    AdminStoreDetailResponse,
    AdminStoreListResponse,
    AdminStoreModerationUpdate,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserStatusUpdate,
    AdminUserSummaryResponse,
)
from app.modules.admin.service import AdminService
from app.modules.auth.dependencies import require_roles
from app.modules.orders.enums import OrderStatus
from app.modules.seller.enums import StoreStatus
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin Platform"])


# ==============================================================================
# Admin Dashboard
# ==============================================================================

@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    summary="Get consolidated marketplace dashboard metrics",
)
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminDashboardResponse:
    """Retrieve marketplace overview KPIs, counts, and currency-grouped completed sales."""
    return await AdminService.get_dashboard(db)


# ==============================================================================
# Store Moderation
# ==============================================================================

@router.get(
    "/stores",
    response_model=AdminStoreListResponse,
    summary="List stores with administrative moderation filters",
)
async def list_admin_stores(
    status: Optional[StoreStatus] = Query(None, description="Filter by store operational status"),
    is_verified: Optional[bool] = Query(None, description="Filter by trusted verification flag"),
    q: Optional[str] = Query(None, description="Search term for store name, slug, or email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminStoreListResponse:
    """List all marketplace storefronts with pagination and status filters."""
    return await AdminService.list_stores(
        db=db,
        status_filter=status,
        is_verified_filter=is_verified,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stores/{store_id}",
    response_model=AdminStoreDetailResponse,
    summary="Get detailed store information for moderation",
)
async def get_admin_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminStoreDetailResponse:
    """Retrieve detailed store metadata, merchant identity, and catalog counts."""
    return await AdminService.get_store(db, store_id)


@router.patch(
    "/stores/{store_id}/moderation",
    response_model=AdminStoreDetailResponse,
    summary="Moderate store status or verification badge",
)
async def moderate_admin_store(
    store_id: uuid.UUID,
    payload: AdminStoreModerationUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminStoreDetailResponse:
    """
    Update store verification or operational status (ACTIVE, SUSPENDED, REJECTED).
    Verification is decoupled from operational status.
    """
    return await AdminService.moderate_store(db, store_id, payload)


# ==============================================================================
# User Management
# ==============================================================================

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List users with administrative filters",
)
async def list_admin_users(
    role: Optional[UserRole] = Query(None, description="Filter by user system role"),
    is_active: Optional[bool] = Query(None, description="Filter by activation status"),
    q: Optional[str] = Query(None, description="Search term for email or name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminUserListResponse:
    """List registered users with pagination and search."""
    return await AdminService.list_users(
        db=db,
        role=role,
        is_active=is_active,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
    summary="Get detailed user profile",
)
async def get_admin_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminUserDetailResponse:
    """Retrieve safe user details and linked merchant store if applicable."""
    return await AdminService.get_user(db, user_id)


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserSummaryResponse,
    summary="Activate or deactivate a user account",
)
async def update_admin_user_status(
    user_id: uuid.UUID,
    payload: AdminUserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminUserSummaryResponse:
    """
    Toggle user active status.
    Guards prevent self-deactivation and deactivating the last active administrator.
    """
    return await AdminService.update_user_status(db, user_id, current_admin, payload)

