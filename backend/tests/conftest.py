"""Pytest configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base

# Try to import fakeredis, fall back to real redis for integration tests
try:
    from fakeredis import aioredis as fake_aioredis
    FAKEREDIS_AVAILABLE = True
except ImportError:
    FAKEREDIS_AVAILABLE = False
    from redis import asyncio as aioredis

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def sync_engine():
    """Create sync test database engine."""
    engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sync_session(sync_engine) -> Generator[Session, None, None]:
    """Create sync test database session."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_db(sync_engine) -> Generator[Session, None, None]:
    """Create test database session (alias for sync_session)."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    from app.models.user import User
    from app.core.security import hash_password
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        name="Test User",
        role="user",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_admin(test_db: Session):
    """Create a test admin user."""
    from app.models.user import User
    from app.core.security import hash_password
    
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPassword123"),
        name="Admin User",
        role="admin",
        is_active=True
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client using fakeredis."""
    if FAKEREDIS_AVAILABLE:
        # Use fakeredis for fast, isolated tests
        client = fake_aioredis.FakeRedis(decode_responses=True)
    else:
        # Fall back to real Redis (requires Redis server running)
        client = aioredis.from_url("redis://localhost:6379/15", decode_responses=True)
    
    yield client
    
    # Cleanup: flush all keys after each test
    await client.flushall()
    await client.aclose()



@pytest_asyncio.fixture
async def async_db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session (alias for async_session)."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user_async(async_db_session: AsyncSession):
    """Create a test user for async tests."""
    from app.models.user import User
    from app.core.security import hash_password
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        name="Test User",
        role="user",
        is_active=True
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def async_client(async_engine):
    """Create async test client."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.database import get_db
    
    # Override database dependency
    async def override_get_db():
        async_session_maker = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_db(async_db_session):
    """Alias for async_db_session for consistency."""
    return async_db_session

