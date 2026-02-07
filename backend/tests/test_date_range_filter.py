"""
Property-based tests for request history date range filtering.

Property: Date Range Filter Correctness
Validates: Requirements 8.8

Tests that only requests within date range are returned.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.user import User
from app.models.request import Request
from app.core.security import create_access_token


def create_auth_headers(user_id: str) -> dict:
    """Helper to create auth headers."""
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@given(
    days_before_start=st.integers(min_value=1, max_value=10),
    days_in_range=st.integers(min_value=1, max_value=10),
    days_after_end=st.integers(min_value=1, max_value=10),
    num_before=st.integers(min_value=0, max_value=5),
    num_in_range=st.integers(min_value=0, max_value=10),
    num_after=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=30, deadline=None)
async def test_date_range_filter_correctness(
    days_before_start,
    days_in_range,
    days_after_end,
    num_before,
    num_in_range,
    num_after
):
    """
    Property: For any date range [start, end], the filtered history should contain
    only requests where start <= created_at <= end.
    
    **Validates: Requirements 8.8**
    """
    # Import here to avoid module loading issues
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.models.base import Base
    
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Define date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=days_before_start + days_in_range)
    end_date = now - timedelta(days=days_before_start)
    
    async with async_session_maker() as session:
        # Create test user
        from app.core.security import hash_password
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("TestPassword123"),
            name="Test User",
            role="user",
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Create auth headers
        auth_headers = create_auth_headers(str(test_user.id))
        
        # Create requests before the range
        before_ids = set()
        for i in range(num_before):
            created_at = start_date - timedelta(days=i+1)
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Request before range {i}",
                execution_mode="balanced",
                status="completed",
                created_at=created_at
            )
            session.add(db_request)
            before_ids.add(str(db_request.id))
        
        # Create requests within the range
        in_range_ids = set()
        for i in range(num_in_range):
            # Distribute requests evenly within the range
            offset_hours = (days_in_range * 24 * i) // max(num_in_range, 1)
            created_at = start_date + timedelta(hours=offset_hours)
            # Ensure it's within range
            if created_at > end_date:
                created_at = end_date - timedelta(hours=1)
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Request in range {i}",
                execution_mode="balanced",
                status="completed",
                created_at=created_at
            )
            session.add(db_request)
            in_range_ids.add(str(db_request.id))
        
        # Create requests after the range
        after_ids = set()
        for i in range(num_after):
            created_at = end_date + timedelta(days=i+1)
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Request after range {i}",
                execution_mode="balanced",
                status="completed",
                created_at=created_at
            )
            session.add(db_request)
            after_ids.add(str(db_request.id))
        
        await session.commit()
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make request with date range filter
        response = await client.get(
            "/api/v1/council/history",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
                "limit": 100
            },
            headers=auth_headers
        )
    
    app.dependency_overrides.clear()
    
    # Should succeed
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify all returned items are within the date range
    returned_ids = set()
    for item in data["items"]:
        returned_ids.add(item["id"])
        item_date = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
        assert start_date <= item_date <= end_date, \
            f"Item date {item_date} should be within range [{start_date}, {end_date}]"
    
    # Verify all in-range requests are returned
    assert returned_ids == in_range_ids, \
        f"Should return all {len(in_range_ids)} in-range requests, got {len(returned_ids)}"
    
    # Verify no before/after requests are returned
    assert len(returned_ids & before_ids) == 0, \
        "Should not return any requests before the range"
    assert len(returned_ids & after_ids) == 0, \
        "Should not return any requests after the range"
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_start_date_only_filter():
    """
    Property: Filtering with only start_date should return all requests after that date.
    
    **Validates: Requirements 8.8**
    """
    # Import here to avoid module loading issues
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.models.base import Base
    
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    now = datetime.utcnow()
    cutoff_date = now - timedelta(days=5)
    
    async with async_session_maker() as session:
        # Create test user
        from app.core.security import hash_password
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("TestPassword123"),
            name="Test User",
            role="user",
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Create auth headers
        auth_headers = create_auth_headers(str(test_user.id))
        
        # Create requests before cutoff
        for i in range(3):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Old request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=cutoff_date - timedelta(days=i+1)
            )
            session.add(db_request)
        
        # Create requests after cutoff
        after_count = 0
        for i in range(4):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"New request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=cutoff_date + timedelta(days=i+1)
            )
            session.add(db_request)
            after_count += 1
        
        await session.commit()
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter with only start_date
        response = await client.get(
            "/api/v1/council/history",
            params={
                "start_date": cutoff_date.isoformat(),
                "page": 1,
                "limit": 100
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return only requests after cutoff (4 requests)
        assert data["total"] == after_count, \
            f"Should return {after_count} requests after cutoff, got {data['total']}"
        
        # Verify all returned items are after cutoff
        for item in data["items"]:
            item_date = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
            assert item_date >= cutoff_date, \
                f"Item date {item_date} should be >= cutoff {cutoff_date}"
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_end_date_only_filter():
    """
    Property: Filtering with only end_date should return all requests before that date.
    
    **Validates: Requirements 8.8**
    """
    # Import here to avoid module loading issues
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.models.base import Base
    
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    now = datetime.utcnow()
    cutoff_date = now - timedelta(days=5)
    
    async with async_session_maker() as session:
        # Create test user
        from app.core.security import hash_password
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("TestPassword123"),
            name="Test User",
            role="user",
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Create auth headers
        auth_headers = create_auth_headers(str(test_user.id))
        
        # Create requests before cutoff
        before_count = 0
        for i in range(3):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Old request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=cutoff_date - timedelta(days=i+1)
            )
            session.add(db_request)
            before_count += 1
        
        # Create requests after cutoff
        for i in range(4):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"New request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=cutoff_date + timedelta(days=i+1)
            )
            session.add(db_request)
        
        await session.commit()
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter with only end_date
        response = await client.get(
            "/api/v1/council/history",
            params={
                "end_date": cutoff_date.isoformat(),
                "page": 1,
                "limit": 100
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return only requests before cutoff (3 requests)
        assert data["total"] == before_count, \
            f"Should return {before_count} requests before cutoff, got {data['total']}"
        
        # Verify all returned items are before cutoff
        for item in data["items"]:
            item_date = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
            assert item_date <= cutoff_date, \
                f"Item date {item_date} should be <= cutoff {cutoff_date}"
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_invalid_date_format():
    """
    Property: Invalid date formats should be rejected.
    
    **Validates: Requirements 8.8**
    """
    # Import here to avoid module loading issues
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.models.base import Base
    
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Create test user
        from app.core.security import hash_password
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("TestPassword123"),
            name="Test User",
            role="user",
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Create auth headers
        auth_headers = create_auth_headers(str(test_user.id))
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test invalid start_date format
        response = await client.get(
            "/api/v1/council/history",
            params={"start_date": "not-a-date", "page": 1, "limit": 20},
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test invalid end_date format
        response = await client.get(
            "/api/v1/council/history",
            params={"end_date": "2024-13-45", "page": 1, "limit": 20},
            headers=auth_headers
        )
        assert response.status_code == 400
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()
