"""Admin endpoints for user management and system monitoring."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_admin_user
from app.models.user import User
from app.models.request import Request

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


# Pydantic schemas
class UserListItem(BaseModel):
    """User list item schema for admin user list."""
    model_config = {"from_attributes": True}
    
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str
    total_requests: int


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: list[UserListItem]
    total: int
    page: int
    pages: int


class UserUpdateRequest(BaseModel):
    """User update request schema for admin."""
    is_active: Optional[bool] = None
    role: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate role is either 'user' or 'admin'."""
        if v is not None and v not in ['user', 'admin']:
            raise ValueError('Role must be either "user" or "admin"')
        return v


class UserDetailResponse(BaseModel):
    """Detailed user information for admin."""
    model_config = {"from_attributes": True}
    
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    total_requests: int
    recent_requests: list[dict]


class AuditLogEntry(BaseModel):
    """Audit log entry for admin actions."""
    timestamp: str
    admin_id: str
    admin_email: str
    action: str
    target_user_id: str
    target_user_email: str
    changes: dict


@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get paginated list of all users.
    
    Requires admin role for access.
    
    Args:
        page: Page number (1-indexed)
        limit: Number of items per page (max 100)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Paginated list of users with email, registration date, total requests, and account status
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Query users with request count
    users_query = (
        db.query(
            User,
            func.count(Request.id).label('total_requests')
        )
        .outerjoin(Request, User.id == Request.user_id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )
    
    # Get total count
    total = db.query(User).count()
    
    # Get paginated results
    users_with_counts = users_query.offset(offset).limit(limit).all()
    
    # Format response
    user_items = []
    for user, request_count in users_with_counts:
        user_items.append(UserListItem(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            total_requests=request_count
        ))
    
    # Calculate total pages
    pages = (total + limit - 1) // limit
    
    return UserListResponse(
        users=user_items,
        total=total,
        page=page,
        pages=pages
    )


@router.patch("/users/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Update user account (enable/disable, change role).
    
    Requires admin role for access.
    Logs all admin actions for audit purposes.
    
    Args:
        user_id: User ID to update
        update_data: Update data (is_active, role)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to modify own account
    """
    # Convert string UUID to UUID object
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from modifying their own account
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account"
        )
    
    # Track changes for audit log
    changes = {}
    
    # Update is_active if provided
    if update_data.is_active is not None:
        old_value = user.is_active
        user.is_active = update_data.is_active
        changes['is_active'] = {'old': old_value, 'new': update_data.is_active}
    
    # Update role if provided
    if update_data.role is not None:
        old_value = user.role
        user.role = update_data.role
        changes['role'] = {'old': old_value, 'new': update_data.role}
    
    # Update timestamp
    user.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    # Log admin action for audit
    audit_entry = AuditLogEntry(
        timestamp=datetime.utcnow().isoformat(),
        admin_id=str(current_admin.id),
        admin_email=current_admin.email,
        action="update_user",
        target_user_id=str(user.id),
        target_user_email=user.email,
        changes=changes
    )
    
    logger.info(f"Admin action: {audit_entry.model_dump_json()}")
    
    return {
        "message": "User updated successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role
        }
    }


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed user information including request history and statistics.
    
    Requires admin role for access.
    
    Args:
        user_id: User ID to retrieve
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Detailed user information with request history
        
    Raises:
        HTTPException 404: If user not found
    """
    # Convert string UUID to UUID object
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get total request count
    total_requests = db.query(func.count(Request.id)).filter(
        Request.user_id == user_uuid
    ).scalar()
    
    # Get recent requests (last 10)
    recent_requests = (
        db.query(Request)
        .filter(Request.user_id == user_uuid)
        .order_by(Request.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Format recent requests
    recent_requests_data = []
    for req in recent_requests:
        recent_requests_data.append({
            "id": str(req.id),
            "content": req.content[:100] + "..." if len(req.content) > 100 else req.content,
            "execution_mode": req.execution_mode,
            "status": req.status,
            "created_at": req.created_at.isoformat(),
            "completed_at": req.completed_at.isoformat() if req.completed_at else None
        })
    
    return UserDetailResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        total_requests=total_requests or 0,
        recent_requests=recent_requests_data
    )
