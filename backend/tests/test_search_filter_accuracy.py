"""
Property-based tests for request history search filtering.

Property: Search Filter Accuracy
Validates: Requirements 8.6

Tests that search returns only matching requests.
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
    search_term=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    num_matching=st.integers(min_value=0, max_value=10),
    num_non_matching=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=30, deadline=None)
async def test_search_returns_only_matching_requests(
    search_term,
    num_matching,
    num_non_matching
):
    """
    Property: For any search term S, the filtered history should contain only requests
    where the content contains S as a substring (case-insensitive).
    
    **Validates: Requirements 8.6**
    """
    # Skip if search term is empty or whitespace only
    assume(search_term.strip())
    
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
        
        # Create matching requests (contain search term)
        matching_ids = set()
        for i in range(num_matching):
            content = f"This request contains {search_term} in the middle {i}"
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=content,
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            session.add(db_request)
            matching_ids.add(str(db_request.id))
        
        # Create non-matching requests (do not contain search term)
        non_matching_ids = set()
        for i in range(num_non_matching):
            # Use a different string that doesn't contain the search term
            content = f"Different content without the term {i} xyz"
            # Make sure it doesn't accidentally contain the search term
            if search_term.lower() not in content.lower():
                db_request = Request(
                    id=uuid4(),
                    user_id=test_user.id,
                    content=content,
                    execution_mode="balanced",
                    status="completed",
                    created_at=datetime.utcnow() - timedelta(hours=num_matching + i)
                )
                session.add(db_request)
                non_matching_ids.add(str(db_request.id))
        
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
        # Make request with search filter
        response = await client.get(
            "/api/v1/council/history",
            params={"search": search_term, "page": 1, "limit": 100},
            headers=auth_headers
        )
    
    app.dependency_overrides.clear()
    
    # Should succeed
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify all returned items contain the search term (case-insensitive)
    returned_ids = set()
    for item in data["items"]:
        returned_ids.add(item["id"])
        # Verify the content contains the search term (case-insensitive)
        assert search_term.lower() in item["content"].lower(), \
            f"Item content '{item['content']}' should contain search term '{search_term}'"
    
    # Verify all matching requests are returned
    assert returned_ids == matching_ids, \
        f"Should return all {len(matching_ids)} matching requests, got {len(returned_ids)}"
    
    # Verify no non-matching requests are returned
    assert len(returned_ids & non_matching_ids) == 0, \
        "Should not return any non-matching requests"
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_search_case_insensitive():
    """
    Property: Search should be case-insensitive.
    
    **Validates: Requirements 8.6**
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
        
        # Create requests with different cases
        request_contents = [
            "This has UPPERCASE text",
            "This has lowercase text",
            "This has MixedCase text"
        ]
        
        for content in request_contents:
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=content,
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow()
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
        # Search with lowercase
        response = await client.get(
            "/api/v1/council/history",
            params={"search": "text", "page": 1, "limit": 100},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find all 3 requests regardless of case
        assert data["total"] == 3, \
            f"Should find all 3 requests with 'text', got {data['total']}"
        
        # Search with uppercase
        response = await client.get(
            "/api/v1/council/history",
            params={"search": "TEXT", "page": 1, "limit": 100},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still find all 3 requests
        assert data["total"] == 3, \
            f"Should find all 3 requests with 'TEXT', got {data['total']}"
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_search_empty_string_returns_all():
    """
    Property: Empty search string should return all requests.
    
    **Validates: Requirements 8.6**
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
        
        # Create 5 requests with different content
        for i in range(5):
            db_request = Request(
                id=uuid4(),
                user_id=test_user.id,
                content=f"Request number {i}",
                execution_mode="balanced",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=i)
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
        # Search with empty string
        response = await client.get(
            "/api/v1/council/history",
            params={"search": "", "page": 1, "limit": 100},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return all 5 requests
        assert data["total"] == 5, \
            f"Empty search should return all 5 requests, got {data['total']}"
        
        # Search with no search parameter
        response = await client.get(
            "/api/v1/council/history",
            params={"page": 1, "limit": 100},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should also return all 5 requests
        assert data["total"] == 5, \
            f"No search parameter should return all 5 requests, got {data['total']}"
    
    app.dependency_overrides.clear()
    
    # Cleanup
    await engine.dispose()
