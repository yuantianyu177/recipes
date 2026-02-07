import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.auth import create_access_token
from app.main import app
from app.models.models import Recipe, Tag, Ingredient  # noqa: F401 - ensure models loaded

TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture
async def db_engine():
    """Create a fresh async engine per test function, drop and recreate all tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=5)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Provide a database session for each test."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    """Provide an async HTTP client with overridden DB dependency."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return authorization headers with a valid admin JWT token."""
    token = create_access_token(data={"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}
