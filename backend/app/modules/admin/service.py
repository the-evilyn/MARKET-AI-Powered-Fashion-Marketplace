from datetime import datetime, timezone
from decimal import Decimal
import math
import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.admin.schemas import (
    AdminCurrencySalesResponse,
    AdminDashboardResponse,
    AdminOrderDetailResponse,
    AdminOrderItemResponse,
    AdminOrderListResponse,
    AdminOrderSummaryResponse,
    AdminPaymentSummaryResponse,
    AdminStoreDetailResponse,
    AdminStoreListResponse,
    AdminStoreModerationUpdate,
    AdminStoreSummaryResponse,
    AdminSubOrderResponse,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserStatusUpdate,
    AdminUserSummaryResponse,
)
from app.modules.catalog.enums import ProductStatus
from app.modules.catalog.models import Product
from app.modules.orders.enums import OrderStatus
from app.modules.orders.models import Order, OrderItem, SubOrder
from app.modules.payments.enums import PaymentStatus
from app.modules.payments.models import Payment
from app.modules.seller.enums import StoreStatus
from app.modules.seller.models import Store
from app.modules.users.enums import UserRole
from app.modules.users.models import User


class AdminService:
    """Service layer implementing marketplace administration, moderation, and KPI derivation."""

    # ==========================================================================
    # Dashboard & KPIs
    # ==========================================================================

    @staticmethod
    async def get_dashboard(db: AsyncSession) -> AdminDashboardResponse:
        """
        Derive marketplace-wide KPIs using efficient database aggregate queries.
        Rules:
        - Only counts distinct parent orders for total order counts.
        - Completed revenue is calculated exclusively from completed payments.
        - Multi-currency totals are partitioned by currency to prevent currency cross-contamination.
        - Handled safely when the database contains no records.
        """
        # 1. User metrics
        total_users_stmt = select(func.count(User.id))
        total_users = (await db.execute(total_users_stmt)).scalar() or 0

        active_users_stmt = select(func.count(User.id)).where(User.is_active.is_(True))
        active_users = (await db.execute(active_users_stmt)).scalar() or 0

        total_sellers_stmt = select(func.count(User.id)).where(User.role == UserRole.SELLER)
        total_sellers = (await db.execute(total_sellers_stmt)).scalar() or 0

        active_sellers_stmt = select(func.count(User.id)).where(
            User.role == UserRole.SELLER,
            User.is_active.is_(True),
        )
        active_sellers = (await db.execute(active_sellers_stmt)).scalar() or 0

        # 2. Store metrics
        total_stores_stmt = select(func.count(Store.id))
        total_stores = (await db.execute(total_stores_stmt)).scalar() or 0

        stores_awaiting_stmt = select(func.count(Store.id)).where(Store.status == StoreStatus.PENDING)
        stores_awaiting_review = (await db.execute(stores_awaiting_stmt)).scalar() or 0

        verified_stores_stmt = select(func.count(Store.id)).where(Store.is_verified.is_(True))
        verified_stores = (await db.execute(verified_stores_stmt)).scalar() or 0

        # 3. Order metrics
        total_orders_stmt = select(func.count(Order.id))
        total_orders = (await db.execute(total_orders_stmt)).scalar() or 0

        order_status_stmt = select(Order.status, func.count(Order.id)).group_by(Order.status)
        order_status_res = await db.execute(order_status_stmt)
        status_counts_raw = dict(order_status_res.all())

        orders_by_status: Dict[str, int] = {
            s.value: status_counts_raw.get(s, 0)
            for s in OrderStatus
        }

        # 4. Paid revenue grouped by currency (strictly completed payments on parent orders)
        sales_stmt = (
            select(
                Payment.currency,
                func.coalesce(func.sum(Payment.amount), Decimal("0.00")).label("total_sales"),
                func.count(Payment.id).label("order_count"),
            )
            .where(Payment.status == PaymentStatus.COMPLETED)
            .group_by(Payment.currency)
            .order_by(Payment.currency)
        )
        sales_res = await db.execute(sales_stmt)
        sales_by_currency: List[AdminCurrencySalesResponse] = [
            AdminCurrencySalesResponse(
                currency=row.currency,
                total_sales=row.total_sales,
                order_count=row.order_count,
            )
            for row in sales_res.all()
        ]

        total_paid_orders = sum(s.order_count for s in sales_by_currency)

        return AdminDashboardResponse(
            total_users=total_users,
            active_users=active_users,
            total_sellers=total_sellers,
            active_sellers=active_sellers,
            total_stores=total_stores,
            stores_awaiting_review=stores_awaiting_review,
            verified_stores=verified_stores,
            total_orders=total_orders,
            orders_by_status=orders_by_status,
            sales_by_currency=sales_by_currency,
            total_paid_orders=total_paid_orders,
        )

    # ==========================================================================
    # Store Moderation
    # ==========================================================================

    @staticmethod
    async def list_stores(
        db: AsyncSession,
        status_filter: Optional[StoreStatus] = None,
        is_verified_filter: Optional[bool] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminStoreListResponse:
        """Paginated list of marketplace stores with moderation filters."""
        stmt = select(Store).options(selectinload(Store.user))

        if status_filter is not None:
            stmt = stmt.where(Store.status == status_filter)
        if is_verified_filter is not None:
            stmt = stmt.where(Store.is_verified == is_verified_filter)
        if q:
            search_pattern = f"%{q.strip()}%"
            stmt = stmt.join(User, Store.seller_id == User.id).where(
                or_(
                    Store.store_name.ilike(search_pattern),
                    Store.slug.ilike(search_pattern),
                    Store.contact_email.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Paginate
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Store.created_at.desc()).offset(offset).limit(page_size)

        stores = (await db.execute(stmt)).scalars().all()

        items = [
            AdminStoreSummaryResponse(
                id=s.id,
                seller_id=s.seller_id,
                store_name=s.store_name,
                slug=s.slug,
                bio=s.bio,
                logo_url=s.logo_url,
                banner_url=s.banner_url,
                contact_email=s.contact_email,
                contact_phone=s.contact_phone,
                status=s.status,
                is_verified=s.is_verified,
                created_at=s.created_at,
                updated_at=s.updated_at,
                seller_email=s.user.email if s.user else None,
                seller_name=f"{s.user.first_name} {s.user.last_name}".strip() if s.user else None,
            )
            for s in stores
        ]

        return AdminStoreListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_store(db: AsyncSession, store_id: uuid.UUID) -> AdminStoreDetailResponse:
        """Retrieve full store details including product counts."""
        stmt = select(Store).options(selectinload(Store.user)).where(Store.id == store_id)
        res = await db.execute(stmt)
        store = res.scalar_one_or_none()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id '{store_id}' was not found.",
            )

        # Product count aggregates
        total_p_stmt = select(func.count(Product.id)).where(Product.seller_id == store.seller_id)
        total_products_count = (await db.execute(total_p_stmt)).scalar() or 0

        active_p_stmt = select(func.count(Product.id)).where(
            Product.seller_id == store.seller_id,
            Product.status == ProductStatus.ACTIVE,
            Product.is_active.is_(True),
        )
        active_products_count = (await db.execute(active_p_stmt)).scalar() or 0

        return AdminStoreDetailResponse(
            id=store.id,
            seller_id=store.seller_id,
            store_name=store.store_name,
            slug=store.slug,
            bio=store.bio,
            logo_url=store.logo_url,
            banner_url=store.banner_url,
            contact_email=store.contact_email,
            contact_phone=store.contact_phone,
            status=store.status,
            is_verified=store.is_verified,
            created_at=store.created_at,
            updated_at=store.updated_at,
            seller_email=store.user.email if store.user else None,
            seller_name=f"{store.user.first_name} {store.user.last_name}".strip() if store.user else None,
            active_products_count=active_products_count,
            total_products_count=total_products_count,
        )

    @staticmethod
    async def moderate_store(
        db: AsyncSession,
        store_id: uuid.UUID,
        payload: AdminStoreModerationUpdate,
    ) -> AdminStoreDetailResponse:
        """
        Execute authorized moderation update on a store.
        Rules:
        - Must provide at least one moderation field (is_verified or status).
        - Verification update does NOT modify status (e.g. verifying a SUSPENDED store leaves it SUSPENDED).
        - Status update strictly follows allowed transitions:
            ACTIVE -> SUSPENDED
            SUSPENDED -> ACTIVE
            PENDING -> ACTIVE or REJECTED
            REJECTED -> ACTIVE
        - Invalid transitions raise HTTP 400.
        """
        if payload.is_verified is None and payload.status is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one moderation field (is_verified or status) must be provided.",
            )

        stmt = select(Store).options(selectinload(Store.user)).where(Store.id == store_id)
        res = await db.execute(stmt)
        store = res.scalar_one_or_none()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id '{store_id}' was not found.",
            )

        # 1. Update verification flag if provided (decoupled from status)
        if payload.is_verified is not None:
            store.is_verified = payload.is_verified

        # 2. Update status if provided
        if payload.status is not None and payload.status != store.status:
            allowed_transitions = {
                StoreStatus.ACTIVE: {StoreStatus.SUSPENDED},
                StoreStatus.SUSPENDED: {StoreStatus.ACTIVE},
                StoreStatus.PENDING: {StoreStatus.ACTIVE, StoreStatus.REJECTED},
                StoreStatus.REJECTED: {StoreStatus.ACTIVE},
            }
            valid_targets = allowed_transitions.get(store.status, set())
            if payload.status not in valid_targets:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition store status from '{store.status.value}' to '{payload.status.value}'.",
                )
            store.status = payload.status

        store.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(store)

        return await AdminService.get_store(db, store_id)

    # ==========================================================================
    # User Management
    # ==========================================================================

    @staticmethod
    async def list_users(
        db: AsyncSession,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminUserListResponse:
        """Paginated list of registered users with administrative filters."""
        stmt = select(User)

        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if q:
            search_pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        users = (await db.execute(stmt)).scalars().all()

        items = [
            AdminUserSummaryResponse(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at,
                updated_at=u.updated_at,
                last_login_at=u.last_login_at,
            )
            for u in users
        ]

        return AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_user(db: AsyncSession, user_id: uuid.UUID) -> AdminUserDetailResponse:
        """Get safe user detail with linked storefront if user is a merchant."""
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{user_id}' was not found.",
            )

        store_stmt = select(Store).where(Store.seller_id == user_id)
        store = (await db.execute(store_stmt)).scalar_one_or_none()

        return AdminUserDetailResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            store_id=store.id if store else None,
            store_name=store.store_name if store else None,
            store_slug=store.slug if store else None,
        )

    @staticmethod
    async def update_user_status(
        db: AsyncSession,
        user_id: uuid.UUID,
        current_admin: User,
        payload: AdminUserStatusUpdate,
    ) -> AdminUserSummaryResponse:
        """
        Activate or deactivate a user account with strict administrator protections:
        1. Prevents self-deactivation.
        2. Prevents deactivating the last active administrator.
        3. Never modifies user roles.
        """
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{user_id}' was not found.",
            )

        # 1. Guard against self-deactivation
        if user.id == current_admin.id and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account.",
            )

        # 2. Guard against deactivating the last active administrator
        if user.role == UserRole.ADMIN and not payload.is_active:
            active_admin_stmt = select(func.count(User.id)).where(
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
                User.id != user.id,
            )
            other_active_admins = (await db.execute(active_admin_stmt)).scalar() or 0
            if other_active_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active administrator.",
                )

        user.is_active = payload.is_active
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        return AdminUserSummaryResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    # ==========================================================================
    # Global Orders Supervision
    # ==========================================================================

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        status_filter: Optional[OrderStatus] = None,
        customer_id: Optional[uuid.UUID] = None,
        seller_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminOrderListResponse:
        """Paginated list of orders across all customers and sellers."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.payment),
                selectinload(Order.sub_orders),
            )
        )

        if status_filter is not None:
            stmt = stmt.where(Order.status == status_filter)
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
        if seller_id is not None:
            seller_order_subquery = (
                select(SubOrder.order_id)
                .where(SubOrder.seller_id == seller_id)
                .scalar_subquery()
            )
            stmt = stmt.where(Order.id.in_(seller_order_subquery))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(page_size)

        orders = (await db.execute(stmt)).scalars().all()

        items = [
            AdminOrderSummaryResponse(
                id=o.id,
                order_number=o.order_number,
                customer_id=o.customer_id,
                customer_email=o.customer.email if o.customer else None,
                customer_name=f"{o.customer.first_name} {o.customer.last_name}".strip() if o.customer else None,
                status=o.status,
                subtotal=o.subtotal,
                total=o.total,
                currency=o.currency,
                payment_status=o.payment.status if o.payment else None,
                sub_orders_count=len(o.sub_orders),
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in orders
        ]

        return AdminOrderListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_order(db: AsyncSession, order_id: uuid.UUID) -> AdminOrderDetailResponse:
        """Retrieve complete order details including sub-orders, items, and safe payment info."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.payment),
                selectinload(Order.items),
                selectinload(Order.sub_orders).selectinload(SubOrder.seller),
                selectinload(Order.sub_orders).selectinload(SubOrder.items),
            )
            .where(Order.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id '{order_id}' was not found.",
            )

        payment_summary = None
        if order.payment:
            payment_summary = AdminPaymentSummaryResponse(
                id=order.payment.id,
                provider=order.payment.provider,
                status=order.payment.status,
                amount=order.payment.amount,
                currency=order.payment.currency,
                provider_payment_id=order.payment.provider_payment_id,
                created_at=order.payment.created_at,
            )

        sub_orders = [
            AdminSubOrderResponse(
                id=so.id,
                order_id=so.order_id,
                seller_id=so.seller_id,
                seller_email=so.seller.email if so.seller else None,
                sub_order_number=so.sub_order_number,
                status=so.status,
                subtotal=so.subtotal,
                shipping_amount=so.shipping_amount,
                total=so.total,
                currency=so.currency,
                carrier=so.carrier,
                tracking_number=so.tracking_number,
                shipped_at=so.shipped_at,
                delivered_at=so.delivered_at,
                created_at=so.created_at,
                items=[
                    AdminOrderItemResponse(
                        id=it.id,
                        order_id=it.order_id,
                        sub_order_id=it.sub_order_id,
                        seller_id=it.seller_id,
                        variant_id=it.variant_id,
                        product_name=it.product_name,
                        sku=it.sku,
                        color=it.color,
                        size=it.size,
                        unit_price=it.unit_price,
                        quantity=it.quantity,
                        line_total=it.line_total,
                        created_at=it.created_at,
                    )
                    for it in (so.items or [])
                ],
            )
            for so in (order.sub_orders or [])
        ]

        items = [
            AdminOrderItemResponse(
                id=it.id,
                order_id=it.order_id,
                sub_order_id=it.sub_order_id,
                seller_id=it.seller_id,
                variant_id=it.variant_id,
                product_name=it.product_name,
                sku=it.sku,
                color=it.color,
                size=it.size,
                unit_price=it.unit_price,
                quantity=it.quantity,
                line_total=it.line_total,
                created_at=it.created_at,
            )
            for it in (order.items or [])
        ]

        return AdminOrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_email=order.customer.email if order.customer else None,
            customer_name=f"{order.customer.first_name} {order.customer.last_name}".strip() if order.customer else None,
            status=order.status,
            subtotal=order.subtotal,
            total=order.total,
            currency=order.currency,
            payment=payment_summary,
            sub_orders=sub_orders,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
