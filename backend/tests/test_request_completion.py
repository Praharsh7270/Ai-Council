"""
Property-based tests for request completion updates history.

Property 22: Request Completion Updates History
Validates: Requirements 5.9
Test that completed requests update status and create Response
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from uuid import UUID

from app.models.request import Request
from app.models.response import Response


# Strategy for generating valid request content (1-5000 chars)
valid_content_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs',)),  # Exclude surrogates
    min_size=1,
    max_size=100  # Keep it short for faster tests
)

# Strategy for generating valid execution modes
valid_execution_mode_strategy = st.sampled_from(["fast", "balanced", "best_quality"])

# Strategy for generating confidence scores (0.0-1.0)
confidence_strategy = st.floats(min_value=0.0, max_value=1.0)

# Strategy for generating costs (0.0-10.0)
cost_strategy = st.floats(min_value=0.0, max_value=10.0)

# Strategy for generating execution times (0.1-300.0 seconds)
execution_time_strategy = st.floats(min_value=0.1, max_value=300.0)


@pytest.mark.asyncio
@given(
    content=valid_content_strategy,
    execution_mode=valid_execution_mode_strategy,
    confidence=confidence_strategy,
    cost=cost_strategy,
    execution_time=execution_time_strategy
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_request_completion_creates_response(
    content: str,
    execution_mode: str,
    confidence: float,
    cost: float,
    execution_time: float,
    async_db_session,
    test_user_async
):
    """
    Property 22: Request Completion Updates History
    
    Test that completed requests update status and create Response record.
    
    **Validates: Requirements 5.9**
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
    
    # Simulate request completion
    request.status = "completed"
    request.completed_at = datetime.utcnow()
    
    # Create response record
    response = Response(
        request_id=request.id,
        content="Test response content",
        confidence=confidence,
        total_cost=cost,
        execution_time=execution_time,
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
    await async_db_session.refresh(request)
    await async_db_session.refresh(response)
    
    # Verify request was updated
    assert request.status == "completed"
    assert request.completed_at is not None
    assert isinstance(request.completed_at, datetime)
    
    # Verify response was created
    assert response.id is not None
    assert isinstance(response.id, UUID)
    assert response.request_id == request.id
    assert response.confidence == confidence
    assert response.total_cost == cost
    assert response.execution_time == execution_time
    
    # Verify response has required fields
    assert response.content is not None
    assert response.models_used is not None
    assert response.orchestration_metadata is not None
    
    # Verify confidence is in valid range
    assert 0.0 <= response.confidence <= 1.0
    
    # Verify cost is non-negative
    assert response.total_cost >= 0.0
    
    # Verify execution time is positive
    assert response.execution_time > 0.0


@pytest.mark.asyncio
async def test_request_completion_status_transitions(async_db_session, test_user_async):
    """
    Test that request status transitions correctly from pending to completed.
    
    **Validates: Requirements 5.9**
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
    
    # Verify initial state
    assert request.status == "pending"
    assert request.completed_at is None
    
    # Complete the request
    request.status = "completed"
    request.completed_at = datetime.utcnow()
    
    # Create response
    response = Response(
        request_id=request.id,
        content="Response content",
        confidence=0.95,
        total_cost=0.05,
        execution_time=10.5,
        models_used={"models": ["model1"]},
        orchestration_metadata={"success": True},
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(response)
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Verify final state
    assert request.status == "completed"
    assert request.completed_at is not None
    assert request.completed_at >= request.created_at


@pytest.mark.asyncio
async def test_failed_request_completion(async_db_session, test_user_async):
    """
    Test that failed requests also update status correctly.
    
    **Validates: Requirements 5.9**
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
    
    # Mark request as failed
    request.status = "failed"
    request.completed_at = datetime.utcnow()
    
    await async_db_session.commit()
    await async_db_session.refresh(request)
    
    # Verify failed state
    assert request.status == "failed"
    assert request.completed_at is not None
    assert request.completed_at >= request.created_at


@pytest.mark.asyncio
async def test_response_linked_to_request(async_db_session, test_user_async):
    """
    Test that Response is correctly linked to Request via foreign key.
    
    **Validates: Requirements 5.9**
    """
    # Create a request
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
        content="Response content",
        confidence=0.90,
        total_cost=0.03,
        execution_time=8.2,
        models_used={"models": ["model1", "model2"]},
        orchestration_metadata={"success": True},
        created_at=datetime.utcnow()
    )
    
    async_db_session.add(response)
    await async_db_session.commit()
    await async_db_session.refresh(response)
    
    # Verify relationship
    assert response.request_id == request.id
    
    # Query response by request_id
    from sqlalchemy import select
    result = await async_db_session.execute(
        select(Response).where(Response.request_id == request.id)
    )
    found_response = result.scalar_one_or_none()
    
    assert found_response is not None
    assert found_response.id == response.id
    assert found_response.request_id == request.id
