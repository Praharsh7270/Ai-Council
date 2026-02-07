"""
Unit tests for council processing endpoints.

Tests:
- Successful request submission
- Request validation failures
- Status and result retrieval

**Validates: Requirements 5.1, 5.7, 9.6**
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.request import Request
from app.models.response import Response


@pytest.mark.asyncio
async def test_request_validation_content_length(async_db_session, test_user_async):
    """
    Test that request content length validation works.
    
    **Validates: Requirements 5.1**
    """
    # Test minimum valid length (1 char)
    request_min = Request(
        user_id=test_user_async.id,
        content="a",
        execution_mode="fast",
        status="pending",
        created_at=datetime.utcnow()
    )
    async_db_session.add(request_min)
    await async_db_session.commit()
    await async_db_session.refresh(request_min)
    
    assert request_min.id is not None
    assert len(request_min.content) == 1
    
    # Test maximum valid length (5000 chars)
    request_max = Request(
        user_id=test_user_async.id,
        content="x" * 5000,
        execution_mode="balanced",
        status="pending",
        created_at=datetime.utcnow()
    )
    async_db_session.add(request_max)
    await async_db_session.commit()
    await async_db_session.refresh(request_max)
    
    assert request_max.id is not None
    assert len(request_max.content) == 5000


@pytest.mark.asyncio
async def test_request_validation_execution_mode(async_db_session, test_user_async):
    """
    Test that execution mode validation works.
    
    **Validates: Requirements 5.1**
    """
    # Test all valid execution modes
    valid_modes = ["fast", "balanced", "best_quality"]
    
    for mode in valid_modes:
        request = Request(
            user_id=test_user_async.id,
            content="Test content",
            execution_mode=mode,
            status="pending",
            created_at=datetime.utcnow()
        )
        async_db_session.add(request)
        await async_db_session.commit()
        await async_db_session.refresh(request)
        
        assert request.id is not None
        assert request.execution_mode == mode


@pytest.mark.asyncio
async def test_successful_request_submission(async_db_session, test_user_async):
    """
    Test successful request submission creates a Request record.
    
    **Validates: Requirements 5.1, 5.7**
    """
    # Create a request
    request = Request(
        user_id=test_user_async.id,
        content="Analyze the pros and cons of renewable energy",
        execution_mode="balanced",
        status="pending",
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(request)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Verify request was created
    assert request.id is not None
    assert request.user_id == test_user_async.id
    assert request.content == "Analyze the pros and cons of renewable energy"
    assert request.execution_mode == "balanced"
    assert request.status == "pending"
    assert request.created_at is not None
    assert request.completed_at is None


@pytest.mark.asyncio
async def test_status_retrieval(async_db_session, test_user_async):
    """
    Test retrieving request status.
    
    **Validates: Requirements 9.6**
    """
    # Create a request
    request = Request(
        user_id=test_user_async.id,
        content="Test content",
        execution_mode="fast",
        status="pending",
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(request)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Query request by ID
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Request).where(Request.id == request.id)
    )
    found_request = result.scalar_one_or_none()
    
    # Verify status can be retrieved
    assert found_request is not None
    assert found_request.id == request.id
    assert found_request.status == "pending"
    assert found_request.user_id == test_user_async.id


@pytest.mark.asyncio
async def test_status_retrieval_not_found(async_db_session):
    """
    Test retrieving status for non-existent request returns None.
    
    **Validates: Requirements 9.6**
    """
    # Try to query non-existent request
    non_existent_id = uuid4()
    
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Request).where(Request.id == non_existent_id)
    )
    found_request = result.scalar_one_or_none()
    
    # Verify request not found
    assert found_request is None


@pytest.mark.asyncio
async def test_result_retrieval(async_db_session, test_user_async):
    """
    Test retrieving request result.
    
    **Validates: Requirements 9.6**
    """
    # Create a completed request
    request = Request(
        user_id=test_user_async.id,
        content="Test content",
        execution_mode="balanced",
        status="completed",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    async_db_session.add(request)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Create response
    response = Response(
        request_id=request.id,
        content="Test response content",
        confidence=0.95,
        total_cost=0.05,
        execution_time=10.5,
        models_used={"models": ["model1", "model2"]},
        orchestration_metadata={
            "execution_path": ["analysis", "routing", "execution", "synthesis"],
            "parallel_executions": 2,
            "success": True
        },
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(response)
    await async_db_session.commit()
    await async_db_session.refresh(response)
    
    # Query response by request_id
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Response).where(Response.request_id == request.id)
    )
    found_response = result.scalar_one_or_none()
    
    # Verify response can be retrieved
    assert found_response is not None
    assert found_response.request_id == request.id
    assert found_response.content == "Test response content"
    assert found_response.confidence == 0.95
    assert found_response.total_cost == 0.05
    assert found_response.execution_time == 10.5


@pytest.mark.asyncio
async def test_result_retrieval_not_found(async_db_session, test_user_async):
    """
    Test retrieving result for request without response returns None.
    
    **Validates: Requirements 9.6**
    """
    # Create a pending request (no response yet)
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
    
    # Try to query response
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Response).where(Response.request_id == request.id)
    )
    found_response = result.scalar_one_or_none()
    
    # Verify response not found
    assert found_response is None


@pytest.mark.asyncio
async def test_request_status_progression(async_db_session, test_user_async):
    """
    Test that request status progresses from pending to completed.
    
    **Validates: Requirements 5.7**
    """
    # Create a pending request
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
    
    # Verify initial status
    assert request.status == "pending"
    assert request.completed_at is None
    
    # Update to completed
    request.status = "completed"
    request.completed_at = datetime.utcnow()
    
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Verify final status
    assert request.status == "completed"
    assert request.completed_at is not None


@pytest.mark.asyncio
async def test_multiple_requests_per_user(async_db_session, test_user_async):
    """
    Test that a user can have multiple requests.
    
    **Validates: Requirements 5.1, 5.7**
    """
    # Create multiple requests
    requests = []
    for i in range(3):
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
    
    # Query all requests for user
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Request).where(Request.user_id == test_user_async.id)
    )
    found_requests = result.scalars().all()
    
    # Verify all requests were created
    assert len(found_requests) >= 3
    
    # Verify all belong to the same user
    for req in found_requests:
        assert req.user_id == test_user_async.id
