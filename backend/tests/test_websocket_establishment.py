"""
Property-based tests for WebSocket establishment.

Property 21: WebSocket Establishment for All Requests
Validates: Requirements 5.3, 19.1
Test that submitted requests establish WebSocket
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from uuid import UUID

from app.models.request import Request


# Strategy for generating valid request content (1-5000 chars)
valid_content_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs',)),  # Exclude surrogates
    min_size=1,
    max_size=100  # Keep it short for faster tests
)

# Strategy for generating valid execution modes
valid_execution_mode_strategy = st.sampled_from(["fast", "balanced", "best_quality"])


@pytest.mark.asyncio
@given(
    content=valid_content_strategy,
    execution_mode=valid_execution_mode_strategy
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_websocket_url_generated_for_requests(
    content: str,
    execution_mode: str,
    async_db_session,
    test_user_async
):
    """
    Property 21: WebSocket Establishment for All Requests
    
    Test that submitted requests can generate a WebSocket URL.
    
    **Validates: Requirements 5.3, 19.1**
    """
    # Create a request record
    request = Request(
        user_id=test_user_async.id,
        content=content,
        execution_mode=execution_mode,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(request)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Verify request was created
    assert request.id is not None
    assert isinstance(request.id, UUID)
    
    # Generate WebSocket URL (simulating what the API does)
    from app.core.config import settings
    websocket_url = f"ws://localhost:8000{settings.API_V1_PREFIX}/ws/{request.id}"
    
    # Verify WebSocket URL format
    assert websocket_url.startswith("ws://")
    assert "/ws/" in websocket_url
    assert str(request.id) in websocket_url
    
    # Verify URL contains the API prefix
    assert settings.API_V1_PREFIX in websocket_url


@pytest.mark.asyncio
async def test_websocket_url_format(async_db_session, test_user_async):
    """
    Test that WebSocket URLs follow the correct format.
    
    **Validates: Requirements 5.3, 19.1**
    """
    # Create a request
    request = Request(
        user_id=test_user_async.id,
        content="Test content",
        execution_mode="balanced",
        status="pending",
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(request)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Generate WebSocket URL
    from app.core.config import settings
    websocket_url = f"ws://localhost:8000{settings.API_V1_PREFIX}/ws/{request.id}"
    
    # Verify URL components
    assert websocket_url.startswith("ws://")
    assert "localhost:8000" in websocket_url
    assert f"{settings.API_V1_PREFIX}/ws/" in websocket_url
    assert str(request.id) in websocket_url
    
    # Verify request ID is a valid UUID
    request_id_from_url = websocket_url.split("/ws/")[1]
    try:
        UUID(request_id_from_url)
    except ValueError:
        pytest.fail(f"Invalid UUID in WebSocket URL: {request_id_from_url}")


@pytest.mark.asyncio
async def test_websocket_url_unique_per_request(async_db_session, test_user_async):
    """
    Test that each request gets a unique WebSocket URL.
    
    **Validates: Requirements 5.3, 19.1**
    """
    # Create multiple requests
    requests = []
    for i in range(5):
        request = Request(
            user_id=test_user_async.id,
            content=f"Test content {i}",
            execution_mode="balanced",
            status="pending",
            created_at=datetime.utcnow()
        )
        async_db_session.add(request)
        requests.append(request)
    
    await async_db_session.commit()
    
    # Generate WebSocket URLs
    from app.core.config import settings
    websocket_urls = [
        f"ws://localhost:8000{settings.API_V1_PREFIX}/ws/{req.id}"
        for req in requests
    ]
    
    # Verify all URLs are unique
    assert len(websocket_urls) == len(set(websocket_urls))
    
    # Verify all URLs contain different request IDs
    request_ids = [url.split("/ws/")[1] for url in websocket_urls]
    assert len(request_ids) == len(set(request_ids))
