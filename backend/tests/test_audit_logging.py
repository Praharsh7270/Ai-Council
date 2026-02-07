"""Property-based tests for admin action audit logging.

Property: Admin Action Audit Logging
Validates: Requirements 11.8
Test that all admin actions are logged.
"""

import pytest
import logging
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.core.config import settings
from app.api.admin import update_user, UserUpdateRequest


def create_test_user(db: Session, email: str, role: str = "user", is_active: bool = True) -> tuple[User, str]:
    """Helper to create a test user and return user and token."""
    user = User(
        email=email,
        password_hash=hash_password("testpass123"),
        name="Test User",
        role=role,
        is_active=is_active
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
    target_email=st.emails(),
    is_active_change=st.booleans(),
    role_change=st.sampled_from(["user", "admin"])
)
@pytest.mark.asyncio
async def test_admin_update_user_logs_action(
    db_session: Session,
    target_email: str,
    is_active_change: bool,
    role_change: str
):
    """
    Property: All admin user update actions are logged.
    
    For any admin action that updates a user (changing is_active or role),
    the system should log the action with:
    - Timestamp
    - Admin ID and email
    - Action type
    - Target user ID and email
    - Changes made
    
    Validates: Requirements 11.8
    """
    # Create admin user
    admin, admin_token = create_test_user(db_session, "admin@example.com", role="admin")
    
    # Create target user
    target_user, _ = create_test_user(db_session, target_email, role="user", is_active=True)
    
    # Prepare update data
    update_data = UserUpdateRequest(
        is_active=is_active_change,
        role=role_change
    )
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Call the API function directly
        result = await update_user(
            user_id=str(target_user.id),
            update_data=update_data,
            db=db_session,
            current_admin=admin
        )
        
        # Should succeed
        assert result is not None, "Admin update should succeed"
        assert "message" in result, "Result should contain success message"
        
        # Verify that logger.info was called
        assert mock_logger.info.called, (
            "Admin action should be logged via logger.info"
        )
        
        # Get the logged message
        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) > 0, "At least one log entry should be created"
        
        # Get the last log call (the audit log)
        last_log_call = log_calls[-1]
        log_message = last_log_call[0][0]  # First positional argument
        
        # Verify log message contains "Admin action"
        assert "Admin action:" in log_message, (
            f"Log message should contain 'Admin action:', got: {log_message}"
        )
        
        # Verify log message contains admin information
        assert str(admin.id) in log_message, (
            f"Log should contain admin ID {admin.id}"
        )
        assert admin.email in log_message, (
            f"Log should contain admin email {admin.email}"
        )
        
        # Verify log message contains target user information
        assert str(target_user.id) in log_message, (
            f"Log should contain target user ID {target_user.id}"
        )
        assert target_email in log_message, (
            f"Log should contain target user email {target_email}"
        )
        
        # Verify log message contains action type
        assert "update_user" in log_message, (
            f"Log should contain action type 'update_user'"
        )
        
        # Verify log message contains changes
        assert "changes" in log_message.lower(), (
            f"Log should contain changes information"
        )
    
    # Cleanup
    db_session.delete(target_user)
    db_session.delete(admin)
    db_session.commit()


@hypothesis_settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    is_active_only=st.booleans()
)
@pytest.mark.asyncio
async def test_admin_partial_update_logs_only_changed_fields(
    db_session: Session,
    is_active_only: bool
):
    """
    Property: Admin logs should only include fields that were actually changed.
    
    When an admin updates only some fields (e.g., only is_active or only role),
    the audit log should only include the fields that were changed.
    
    Validates: Requirements 11.8
    """
    # Create admin user
    admin, admin_token = create_test_user(db_session, "admin@example.com", role="admin")
    
    # Create target user
    target_user, _ = create_test_user(db_session, "target@example.com", role="user", is_active=True)
    
    # Prepare update data with only one field
    if is_active_only:
        update_data = UserUpdateRequest(is_active=False)
        expected_field = "is_active"
    else:
        update_data = UserUpdateRequest(role="admin")
        expected_field = "role"
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Call the API function directly
        result = await update_user(
            user_id=str(target_user.id),
            update_data=update_data,
            db=db_session,
            current_admin=admin
        )
        
        # Should succeed
        assert result is not None
        
        # Verify that logger.info was called
        assert mock_logger.info.called
        
        # Get the logged message
        log_calls = mock_logger.info.call_args_list
        last_log_call = log_calls[-1]
        log_message = last_log_call[0][0]
        
        # Verify the expected field is in the log
        assert expected_field in log_message, (
            f"Log should contain changed field '{expected_field}'"
        )
        
        # Verify the log contains old and new values
        assert "old" in log_message.lower() or "new" in log_message.lower(), (
            f"Log should contain old and new values for changed fields"
        )
    
    # Cleanup
    db_session.delete(target_user)
    db_session.delete(admin)
    db_session.commit()


@pytest.mark.asyncio
async def test_admin_action_log_contains_timestamp(
    test_db: Session
):
    """
    Test that admin action logs contain a timestamp.
    
    Every audit log entry should include a timestamp indicating when the action occurred.
    
    Validates: Requirements 11.8
    """
    # Create admin user
    admin, admin_token = create_test_user(test_db, "admin@example.com", role="admin")
    
    # Create target user
    target_user, _ = create_test_user(test_db, "target@example.com", role="user")
    
    # Record time before action
    before_action = datetime.utcnow()
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Call the API function directly
        result = await update_user(
            user_id=str(target_user.id),
            update_data=UserUpdateRequest(is_active=False),
            db=test_db,
            current_admin=admin
        )
        
        # Should succeed
        assert result is not None
        
        # Get the logged message
        log_calls = mock_logger.info.call_args_list
        last_log_call = log_calls[-1]
        log_message = last_log_call[0][0]
        
        # Verify timestamp is present
        assert "timestamp" in log_message.lower(), (
            f"Log should contain a timestamp"
        )
        
        # The log message should contain an ISO format timestamp
        # Look for ISO format pattern (YYYY-MM-DD)
        import re
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.search(iso_pattern, log_message), (
            f"Log should contain ISO format timestamp, got: {log_message}"
        )
    
    # Cleanup
    test_db.delete(target_user)
    test_db.delete(admin)
    test_db.commit()


@pytest.mark.asyncio
async def test_admin_cannot_modify_own_account_no_log(
    test_db: Session
):
    """
    Test that failed admin actions (like trying to modify own account) are not logged as successful actions.
    
    When an admin tries to modify their own account (which should fail),
    no audit log should be created for a successful action.
    
    Validates: Requirements 11.8
    """
    from fastapi import HTTPException
    
    # Create admin user
    admin, admin_token = create_test_user(test_db, "admin@example.com", role="admin")
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Try to modify own account (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                user_id=str(admin.id),
                update_data=UserUpdateRequest(is_active=False),
                db=test_db,
                current_admin=admin
            )
        
        # Should fail with 400
        assert exc_info.value.status_code == 400, (
            f"Admin should not be able to modify own account, got {exc_info.value.status_code}"
        )
        
        # Verify that no audit log was created
        # The logger.info should not be called for failed actions
        if mock_logger.info.called:
            log_calls = mock_logger.info.call_args_list
            for call in log_calls:
                log_message = call[0][0]
                # If there are any logs, they should not be audit logs for this action
                if "Admin action:" in log_message:
                    # This should not happen for failed actions
                    assert False, (
                        f"Failed admin action should not create audit log, but found: {log_message}"
                    )
    
    # Cleanup
    test_db.delete(admin)
    test_db.commit()


@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_updates=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_multiple_admin_actions_all_logged(
    test_db: Session,
    num_updates: int
):
    """
    Property: Multiple admin actions should all be logged.
    
    When an admin performs multiple actions, each action should be logged separately.
    
    Validates: Requirements 11.8
    """
    # Create admin user
    admin, admin_token = create_test_user(test_db, "admin@example.com", role="admin")
    
    # Create multiple target users
    target_users = []
    for i in range(num_updates):
        user, _ = create_test_user(test_db, f"target{i}@example.com", role="user")
        target_users.append(user)
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Perform multiple updates
        for user in target_users:
            result = await update_user(
                user_id=str(user.id),
                update_data=UserUpdateRequest(is_active=False),
                db=test_db,
                current_admin=admin
            )
            assert result is not None
        
        # Verify that logger.info was called for each action
        log_calls = mock_logger.info.call_args_list
        
        # Count audit log entries (those containing "Admin action:")
        audit_logs = [call for call in log_calls if "Admin action:" in call[0][0]]
        
        assert len(audit_logs) >= num_updates, (
            f"Expected at least {num_updates} audit log entries, got {len(audit_logs)}"
        )
        
        # Verify each target user is mentioned in at least one log
        all_logs_text = " ".join([call[0][0] for call in audit_logs])
        for user in target_users:
            assert user.email in all_logs_text, (
                f"User {user.email} should be mentioned in audit logs"
            )
    
    # Cleanup
    for user in target_users:
        test_db.delete(user)
    test_db.delete(admin)
    test_db.commit()


@pytest.mark.asyncio
async def test_audit_log_format_is_json(
    test_db: Session
):
    """
    Test that audit logs are in JSON format for easy parsing.
    
    The audit log should be structured as JSON to facilitate log aggregation and analysis.
    
    Validates: Requirements 11.8
    """
    import json
    
    # Create admin user
    admin, admin_token = create_test_user(test_db, "admin@example.com", role="admin")
    
    # Create target user
    target_user, _ = create_test_user(test_db, "target@example.com", role="user")
    
    # Mock the logger to capture log calls
    with patch('app.api.admin.logger') as mock_logger:
        # Call the API function directly
        result = await update_user(
            user_id=str(target_user.id),
            update_data=UserUpdateRequest(is_active=False),
            db=test_db,
            current_admin=admin
        )
        
        # Should succeed
        assert result is not None
        
        # Get the logged message
        log_calls = mock_logger.info.call_args_list
        last_log_call = log_calls[-1]
        log_message = last_log_call[0][0]
        
        # Extract JSON part (after "Admin action: ")
        if "Admin action:" in log_message:
            json_part = log_message.split("Admin action:", 1)[1].strip()
            
            # Verify it's valid JSON
            try:
                parsed = json.loads(json_part)
                
                # Verify required fields are present
                assert "timestamp" in parsed, "JSON should contain timestamp"
                assert "admin_id" in parsed, "JSON should contain admin_id"
                assert "admin_email" in parsed, "JSON should contain admin_email"
                assert "action" in parsed, "JSON should contain action"
                assert "target_user_id" in parsed, "JSON should contain target_user_id"
                assert "target_user_email" in parsed, "JSON should contain target_user_email"
                assert "changes" in parsed, "JSON should contain changes"
                
            except json.JSONDecodeError as e:
                pytest.fail(f"Audit log should be valid JSON, got error: {e}\nLog: {json_part}")
    
    # Cleanup
    test_db.delete(target_user)
    test_db.delete(admin)
    test_db.commit()
