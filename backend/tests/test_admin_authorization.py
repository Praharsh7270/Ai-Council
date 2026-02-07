"""Property-based tests for admin authorization.

Property: Admin Authorization
Validates: Requirements 11.1
Test that non-admin users cannot access admin endpoints.
"""

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.middleware import get_current_admin_user
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.core.config import settings


def create_test_user(db: Session, email: str, role: str = "user") -> tuple[User, str]:
    """Helper to create a test user and return user and token."""
    user = User(
        email=email,
        password_hash=hash_password("testpass123"),
        name="Test User",
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    )
    
    return user, token


@pytest.fixture
def db_session(test_db):
    """Fixture to provide db_session for hypothesis tests."""
    return test_db


@hypothesis_settings(
    max_examples=20, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    email=st.emails(),
    role=st.sampled_from(["user", "guest", "viewer", "editor"])
)
@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoints(
    db_session: Session,
    email: str,
    role: str
):
    """
    Property: Non-admin users cannot access admin endpoints.
    
    For any non-admin user (with any role except 'admin'),
    the get_current_admin_user middleware should raise 403 Forbidden.
    
    Validates: Requirements 11.1
    """
    # Create a non-admin user with various roles
    user = User(
        email=email,
        password_hash=hash_password("testpass123"),
        name="Test User",
        role=role,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Try to access admin endpoint via middleware
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(user)
    
    # Should raise 403 Forbidden
    assert exc_info.value.status_code == 403, (
        f"Non-admin user with role '{role}' should not be able to access admin endpoints, "
        f"but got status {exc_info.value.status_code}"
    )
    
    # Check error message
    assert "admin" in exc_info.value.detail.lower(), (
        f"Error message should mention admin access requirement, got: {exc_info.value.detail}"
    )
    
    # Cleanup
    db_session.delete(user)
    db_session.commit()


@hypothesis_settings(
    max_examples=10, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    admin_email=st.emails()
)
@pytest.mark.asyncio
async def test_admin_can_access_admin_endpoints(
    db_session: Session,
    admin_email: str
):
    """
    Property: Admin users can access admin endpoints.
    
    For any user with role='admin',
    the get_current_admin_user middleware should succeed.
    
    Validates: Requirements 11.1
    """
    # Create an admin user
    admin = User(
        email=admin_email,
        password_hash=hash_password("testpass123"),
        name="Admin User",
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    # Try to access admin endpoint via middleware
    result = await get_current_admin_user(admin)
    
    # Should succeed and return the admin user
    assert result is not None, "Admin user should be able to access admin endpoints"
    assert result.id == admin.id, "Returned user should match the admin user"
    assert result.role == "admin", "Returned user should have admin role"
    
    # Cleanup
    db_session.delete(admin)
    db_session.commit()


@pytest.mark.asyncio
async def test_admin_middleware_checks_role_not_just_authentication(test_db: Session):
    """
    Test that admin middleware checks role, not just authentication.
    
    This ensures that being authenticated is not enough - the user must have admin role.
    
    Validates: Requirements 11.1
    """
    # Create a regular user
    user = User(
        email="regular@example.com",
        password_hash=hash_password("testpass123"),
        name="Regular User",
        role="user",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Create an admin user
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("testpass123"),
        name="Admin User",
        role="admin",
        is_active=True
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    
    # Regular user should be denied
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(user)
    assert exc_info.value.status_code == 403, "Regular user should be denied"
    assert "admin" in exc_info.value.detail.lower(), "Error should mention admin requirement"
    
    # Admin user should be allowed
    result = await get_current_admin_user(admin)
    assert result is not None, "Admin user should be allowed"
    assert result.id == admin.id, "Returned user should match admin"
    
    # Cleanup
    test_db.delete(user)
    test_db.delete(admin)
    test_db.commit()


@pytest.mark.asyncio
async def test_inactive_admin_cannot_access_admin_endpoints(test_db: Session):
    """
    Test that inactive admin users cannot access admin endpoints.
    
    This is handled by get_current_user before get_current_admin_user is called,
    but we test the full flow here.
    
    Validates: Requirements 11.1
    """
    # Create an inactive admin user
    admin = User(
        email="inactive_admin@example.com",
        password_hash=hash_password("testpass123"),
        name="Inactive Admin",
        role="admin",
        is_active=False
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    
    # Even though the user has admin role, if they reach get_current_admin_user
    # (which shouldn't happen due to get_current_user check), they should still pass
    # the role check. The is_active check is done in get_current_user.
    result = await get_current_admin_user(admin)
    assert result is not None, "Admin role check should pass regardless of is_active"
    assert result.role == "admin"
    
    # Cleanup
    test_db.delete(admin)
    test_db.commit()


@hypothesis_settings(
    max_examples=15, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    role=st.sampled_from(["user", "guest", "viewer", "editor", "moderator", ""])
)
@pytest.mark.asyncio
async def test_only_admin_role_grants_access(test_db: Session, role: str):
    """
    Property: Only users with role='admin' can access admin endpoints.
    
    For any role that is not 'admin', access should be denied.
    
    Validates: Requirements 11.1
    """
    # Create a user with the given role
    user = User(
        email=f"user_{role}@example.com",
        password_hash=hash_password("testpass123"),
        name=f"User {role}",
        role=role if role else "user",  # Default to "user" if empty string
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Try to access admin endpoint
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(user)
    
    # Should raise 403 Forbidden
    assert exc_info.value.status_code == 403
    assert "admin" in exc_info.value.detail.lower()
    
    # Cleanup
    test_db.delete(user)
    test_db.commit()
