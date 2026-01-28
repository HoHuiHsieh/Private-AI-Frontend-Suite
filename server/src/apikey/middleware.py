"""
Middleware for API key validation

Provides authentication using API keys instead of JWT tokens.
API keys should be passed in the Authorization header as: "Bearer sk-..."
"""

from typing import Optional
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_session_factory
from user import User, UserManager
from .manager import ApiKeyManager


# Security scheme for API key authentication
api_key_scheme = HTTPBearer(scheme_name="API Key")

# Initialize managers
apikey_manager = ApiKeyManager()
user_manager = UserManager()


def get_db():
    """Get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate user using API key from Authorization header.
    
    Expected format: Authorization: Bearer sk-<api_key>
    
    Returns:
        User object if API key is valid
    
    Raises:
        HTTPException: If API key is invalid, revoked, expired, or user is inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials or not credentials.credentials:
        raise credentials_exception
    
    api_key = credentials.credentials
    
    # Validate API key format
    if not api_key.startswith("sk-"):
        raise credentials_exception
    
    # Validate API key in database
    api_key_obj = apikey_manager.validate_api_key(db, api_key)
    
    if not api_key_obj:
        raise credentials_exception
    
    # Get user associated with the API key
    user = user_manager.get_user_by_id(db, api_key_obj.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with API key not found"
        )
    
    # Check if user is active
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def validate_api_key_header(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract and validate API key from Authorization header.
    
    This is a simpler alternative to get_current_user_from_api_key
    that only returns the API key string without fetching the user.
    
    Args:
        authorization: Authorization header value
    
    Returns:
        API key string if valid format, None otherwise
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    api_key = parts[1]
    if not api_key.startswith("sk-"):
        return None
    
    return api_key

