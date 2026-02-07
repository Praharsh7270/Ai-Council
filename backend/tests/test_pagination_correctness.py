"""
Property-based tests for request history pagination correctness.

Property: Pagination Correctness
Validates: Requirements 8.5

Tests that pagination returns correct number of items per page
and that page numbers are calculated correctly.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.models.user import User
from app.models.request import Request
from app.core.security import create_access_token


def create_auth_headers(user_id: str) -> dict:
    """Helper to create auth headers."""
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@given(
    total_requests=st.integers(min_value=0, max_value=100),
    page=st.integers(min_value=1, max_value=10),
    limit=st.integers(min_value=1, max_value=50)
)
@settings(max_examples=50, deadline=None)
async def test_pagination_returns_correct_number_of_items(
    total_requests,
    page,
    limit
):
    """
    Property: For any user with N requests, requesting page P with limit L
    should return min(L, N - (P-1)*L) requests, and the total count should equal N.
    
    **Validates: Requirements 8.5**
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
        
        # Create test requests for the user
        for i in range(total_requests):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Test request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=total_requests - i)
            )
            session.add(db_request)
        
        await session.commit()
    
    # Calculate expected number of items
    offset = (page - 1) * limit
    expected_items = max(0, min(limit, total_requests - offset))
    expected_pages = (total_requests + limit - 1) // limit if total_requests > 0 else 0
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make request to history endpoint
        response = await client.get(
            "/api/v1/council/history",
            params={"page": page, "limit": limit},
            headers=auth_headers
        )
    
    app.dependency_overrides.clear()
    
    # Should succeed
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify total count
    assert data["total"] == total_requests, \
        f"Total count should be {total_requests}, got {data['total']}"
    
    # Verify page number
    assert data["page"] == page, \
        f"Page should be {page}, got {data['page']}"
    
    # Verify pages calculation
    assert data["pages"] == expected_pages, \
        f"Pages should be {expected_pages}, got {data['pages']}"
    
    # Verify number of items returned
    assert len(data["items"]) == expected_items, \
        f"Should return {expected_items} items, got {len(data['items'])}"
    
    # If we have items, verify they are valid
    if data["items"]:
        for item in data["items"]:
            assert "id" in item
            assert "content" in item
            assert "execution_mode" in item
            assert "status" in item
            assert "created_at" in item
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
@given(
    total_requests=st.integers(min_value=1, max_value=50),
    limit=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=30, deadline=None)
async def test_pagination_covers_all_requests(
    total_requests,
    limit
):
    """
    Property: Iterating through all pages should return all requests exactly once.
    
    **Validates: Requirements 8.5**
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
        
        # Create test requests for the user
        request_ids = set()
        for i in range(total_requests):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Test request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=total_requests - i)
            )
            session.add(db_request)
            request_ids.add(str(db_request.id))
        
        await session.commit()
    
    # Calculate expected number of pages
    expected_pages = (total_requests + limit - 1) // limit
    
    # Create test client with mocked dependencies
    from app.main import app
    from app.core.database import get_db
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Collect all items from all pages
        collected_ids = set()
        for page in range(1, expected_pages + 1):
            response = await client.get(
                "/api/v1/council/history",
                params={"page": page, "limit": limit},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Collect IDs from this page
            for item in data["items"]:
                collected_ids.add(item["id"])
    
    app.dependency_overrides.clear()
    
    # Verify we collected all requests exactly once
    assert collected_ids == request_ids, \
        f"Should collect all {total_requests} requests, got {len(collected_ids)}"
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_pagination_empty_page_beyond_total():
    """
    Property: Requesting a page beyond the total number of pages should return empty items.
    
    **Validates: Requirements 8.5**
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
        
        # Create 5 test requests
        for i in range(5):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Test request {i}",
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=5 - i)
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
        # Request page 10 with limit 20 (way beyond available data)
        response = await client.get(
            "/api/v1/council/history",
            params={"page": 10, "limit": 20},
            headers=auth_headers
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return empty items but correct total
    assert data["total"] == 5
    assert data["page"] == 10
    assert len(data["items"]) == 0
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_pagination_invalid_parameters():
    """
    Property: Invalid pagination parameters should be rejected.
    
    **Validates: Requirements 8.5**
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
        # Test page < 1
        response = await client.get(
            "/api/v1/council/history",
            params={"page": 0, "limit": 20},
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test limit < 1
        response = await client.get(
            "/api/v1/council/history",
            params={"page": 1, "limit": 0},
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Test limit > 100
        response = await client.get(
            "/api/v1/council/history",
            params={"page": 1, "limit": 101},
            headers=auth_headers
        )
        assert response.status_code == 400
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()
