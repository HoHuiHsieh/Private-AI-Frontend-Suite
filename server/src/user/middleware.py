"""
Middleware for user information extraction from access token
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_session_factory
from .manager import UserManager, TokenManager
from .models import User, AccessToken, TokenData, SCOPES


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Initialize managers
token_manager = TokenManager()
user_manager = UserManager()


def get_db():
    """Get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from the access token in the Authorization header
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = token_manager.decode_token(token)
        if token_data is None:
            raise credentials_exception
            
        username: str = token_data.sub
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = user_manager.get_user(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Check if the current user is active
    """
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Check if the current user has admin scope
    """
    if 'admin' not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
