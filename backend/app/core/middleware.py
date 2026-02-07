"""Authentication and rate limiting middleware for FastAPI."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import verify_token
from app.models.user import User
from app.services.rate_limiter import RateLimiter

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT authentication dependency for FastAPI.
    
    Extracts and validates the JWT token from the Authorization header,
    retrieves the user from the database, and returns the user object.
    
    Args:
        credentials: HTTP Bearer token credentials from Authorization header
        db: Database session
        
    Returns:
        User object if authentication is successful
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 401: If user_id is not found in token payload
        HTTPException 401: If user is not found in database
        HTTPException 403: If user account is disabled
    """
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify and decode token
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token payload
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert string UUID to UUID object
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retrieve user from database
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    
    This is an alias for get_current_user that explicitly checks
    for active users (already done in get_current_user).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user object
    """
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current admin user.
    
    Verifies that the current user has admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Admin user object
        
    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


# Optional: Dependency for optional authentication (allows both authenticated and unauthenticated access)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.
    
    Returns the user if a valid token is provided, otherwise returns None.
    Does not raise an error if no token is provided.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        
        user_uuid = UUID(user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
        
        if user is None or not user.is_active:
            return None
        
        return user
    except (ValueError, Exception):
        return None


async def check_rate_limit(
    request: Request,
    redis: Redis = Depends(get_redis),
    user: Optional[User] = Depends(get_optional_user)
) -> None:
    """
    Rate limiting middleware dependency.
    
    Checks rate limits for the current user or IP address.
    Raises HTTPException 429 if rate limit is exceeded.
    
    Args:
        request: FastAPI request object
        redis: Redis client
        user: Optional authenticated user
        
    Raises:
        HTTPException 429: If rate limit is exceeded
    """
    rate_limiter = RateLimiter(redis)
    
    # Determine identifier and user type
    if user is None:
        # Demo user - use IP address
        client_ip = request.client.host if request.client else "unknown"
        identifier = client_ip
        is_demo = True
        is_admin = False
    else:
        # Authenticated user - use user ID
        identifier = str(user.id)
        is_demo = False
        is_admin = user.role == "admin"
    
    # Check rate limit
    is_allowed, remaining, reset_at = await rate_limiter.check_limit(
        identifier=identifier,
        is_demo=is_demo,
        is_admin=is_admin
    )
    
    # Add rate limit headers to response (will be added by middleware)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_at
    
    if not is_allowed:
        # Calculate retry_after in seconds
        import time
        retry_after = reset_at - int(time.time())
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded",
                "retry_after": retry_after,
                "reset_at": reset_at
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Reset": str(reset_at)
            }
        )
