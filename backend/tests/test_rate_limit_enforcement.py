"""Property-based tests for rate limit enforcement.

**Property 34: Rate Limit Enforcement**
**Validates: Requirements 10.1, 10.3**

This test verifies that the 101st request from an authenticated user
returns a 429 Too Many Requests error, enforcing the rate limit of
100 requests per hour.
"""
import asyncio
import time
from hypothesis import given, strategies as st, settings, Phase, HealthCheck
import pytest

from app.services.rate_limiter import RateLimiter
from app.core.config import settings as app_settings


@pytest.mark.asyncio
@given(
    user_id=st.uuids().map(str),
)
@settings(
    max_examples=10,
    phases=[Phase.generate, Phase.target],
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_rate_limit_enforcement_property(user_id, redis_client):
    """
    Property: The 101st request from an authenticated user returns 429.
    
    **Validates: Requirements 10.1, 10.3**
    
    Given an authenticated user with a unique user_id,
    When they make 100 requests (within the limit),
    Then all 100 requests should be allowed,
    And when they make the 101st request,
    Then it should be rejected with is_allowed=False.
    """
    rate_limiter = RateLimiter(redis_client)
    
    # Ensure we're using the correct limit for authenticated users
    assert rate_limiter.authenticated_limit == 100, "Authenticated limit should be 100"
    
    # Make 100 requests (should all be allowed)
    for i in range(100):
        is_allowed, remaining, reset_at = await rate_limiter.check_limit(
            identifier=user_id,
            is_demo=False,
            is_admin=False
        )
        assert is_allowed, f"Request {i+1} should be allowed"
        assert remaining == 100 - i - 1, f"Remaining should be {100 - i - 1} after request {i+1}"
    
    # The 101st request should be rejected
    is_allowed, remaining, reset_at = await rate_limiter.check_limit(
        identifier=user_id,
        is_demo=False,
        is_admin=False
    )
    assert not is_allowed, "The 101st request should be rejected (rate limit exceeded)"
    assert remaining == 0, "Remaining should be 0 when rate limit is exceeded"
    
    # Verify reset_at is in the future
    current_time = int(time.time())
    assert reset_at > current_time, "Reset time should be in the future"


@pytest.mark.asyncio
@given(
    ip_address=st.from_regex(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', fullmatch=True),
)
@settings(
    max_examples=10,
    phases=[Phase.generate, Phase.target],
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_demo_rate_limit_enforcement_property(ip_address, redis_client):
    """
    Property: The 4th request from a demo user (by IP) returns rejection.
    
    **Validates: Requirements 10.2, 10.3**
    
    Given a demo user (unauthenticated) with a unique IP address,
    When they make 3 requests (within the limit),
    Then all 3 requests should be allowed,
    And when they make the 4th request,
    Then it should be rejected with is_allowed=False.
    """
    rate_limiter = RateLimiter(redis_client)
    
    # Ensure we're using the correct limit for demo users
    assert rate_limiter.demo_limit == 3, "Demo limit should be 3"
    
    # Make 3 requests (should all be allowed)
    for i in range(3):
        is_allowed, remaining, reset_at = await rate_limiter.check_limit(
            identifier=ip_address,
            is_demo=True,
            is_admin=False
        )
        assert is_allowed, f"Demo request {i+1} should be allowed"
        assert remaining == 3 - i - 1, f"Remaining should be {3 - i - 1} after request {i+1}"
    
    # The 4th request should be rejected
    is_allowed, remaining, reset_at = await rate_limiter.check_limit(
        identifier=ip_address,
        is_demo=True,
        is_admin=False
    )
    assert not is_allowed, "The 4th demo request should be rejected (rate limit exceeded)"
    assert remaining == 0, "Remaining should be 0 when rate limit is exceeded"


@pytest.mark.asyncio
@given(
    admin_id=st.uuids().map(str),
)
@settings(
    max_examples=5,
    phases=[Phase.generate, Phase.target],
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_admin_rate_limit_higher_property(admin_id, redis_client):
    """
    Property: Admin users have higher rate limits than regular users.
    
    **Validates: Requirements 10.8**
    
    Given an admin user,
    When they make 101 requests (exceeding regular user limit),
    Then all 101 requests should be allowed (admin limit is 1000),
    Demonstrating that admins have higher limits.
    """
    rate_limiter = RateLimiter(redis_client)
    
    # Ensure we're using the correct limit for admin users
    assert rate_limiter.admin_limit == 1000, "Admin limit should be 1000"
    
    # Make 101 requests (should all be allowed for admin)
    for i in range(101):
        is_allowed, remaining, reset_at = await rate_limiter.check_limit(
            identifier=admin_id,
            is_demo=False,
            is_admin=True
        )
        assert is_allowed, f"Admin request {i+1} should be allowed"
        assert remaining == 1000 - i - 1, f"Remaining should be {1000 - i - 1} after request {i+1}"
    
    # Verify that 101 requests were allowed (proving higher limit)
    # This would have been rejected for a regular user at request 101
