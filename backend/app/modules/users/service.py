import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.enums import UserRole
from app.modules.users.models import User


class UserService:
    """Service layer managing user account queries and persistence."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key UUID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by normalized lowercase email address."""
        normalized_email = email.strip().lower()
        result = await db.execute(select(User).where(User.email == normalized_email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.CUSTOMER,
        is_active: bool = True,
        is_verified: bool = False,
    ) -> User:
        """Create and persist a new user entity."""
        user = User(
            id=uuid.uuid4(),
            email=email.strip().lower(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_last_login(db: AsyncSession, user: User) -> None:
        """Update last_login_at timestamp for authenticated user."""
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
