"""Example protected endpoints demonstrating authentication middleware usage."""

from fastapi import APIRouter, Depends

from app.core.middleware import (
    get_current_user,
    get_current_admin_user,
    get_optional_user,
    check_rate_limit
)
from app.models.user import User

router = APIRouter(prefix="/example", tags=["example"])


@router.get("/protected", dependencies=[Depends(check_rate_limit)])
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """
    Example protected endpoint that requires authentication and rate limiting.
    
    This endpoint demonstrates how to use the authentication middleware
    and rate limiting together.
    Only authenticated users with valid tokens can access this endpoint,
    and they are subject to rate limits.
    
    Args:
        current_user: Current authenticated user (injected by middleware)
        
    Returns:
        User information and a success message
    """
    return {
        "message": "This is a protected endpoint with rate limiting",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role
        }
    }


@router.get("/admin-only", dependencies=[Depends(check_rate_limit)])
async def admin_only_endpoint(current_user: User = Depends(get_current_admin_user)):
    """
    Example admin-only endpoint with rate limiting.
    
    This endpoint demonstrates how to restrict access to admin users only.
    Returns 403 Forbidden if the user is not an admin.
    Admins have higher rate limits than regular users.
    
    Args:
        current_user: Current authenticated admin user (injected by middleware)
        
    Returns:
        Admin-specific information
    """
    return {
        "message": "This is an admin-only endpoint with higher rate limits",
        "admin": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name
        }
    }


@router.get("/optional-auth", dependencies=[Depends(check_rate_limit)])
async def optional_auth_endpoint(current_user: User = Depends(get_optional_user)):
    """
    Example endpoint with optional authentication and rate limiting.
    
    This endpoint can be accessed by both authenticated and unauthenticated users.
    The response varies based on whether the user is authenticated.
    Unauthenticated users (demo) have stricter rate limits (3/hour vs 100/hour).
    
    Args:
        current_user: Current user if authenticated, None otherwise
        
    Returns:
        Different responses based on authentication status
    """
    if current_user:
        return {
            "message": "Welcome back! You have 100 requests per hour.",
            "authenticated": True,
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "name": current_user.name
            }
        }
    else:
        return {
            "message": "Welcome, guest! You have 3 requests per hour.",
            "authenticated": False
        }

