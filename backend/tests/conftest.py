from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings, Settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.catalog.models import (  # noqa: F401
    Brand,
    Category,
    Product,
    ProductVariant,
    ProductMedia,
)
from app.modules.inventory.models import InventoryItem  # noqa: F401


# In-memory SQLite async engine for isolated test runs
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all schema tables before each test and drop them afterward."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated test database session."""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with database dependency override."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def create_user_helper(db_session: AsyncSession):
    """Helper to persist a user directly in test DB."""
    async def _create(
        email: str = "user@example.com",
        password: str = "SecurePass123!",
        role: UserRole = UserRole.CUSTOMER,
        is_active: bool = True,
        is_verified: bool = False,
        first_name: str = "Test",
        last_name: str = "User",
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest.fixture
def auth_headers_helper():
    """Generate HTTP Authorization header dictionary for a given User."""
    def _headers(user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"email": user.email, "role": user.role.value},
        )
        return {"Authorization": f"Bearer {token}"}

    return _headers
