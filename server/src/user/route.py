"""
User API Routes

ENDPOINTS

1. POST /api/login
   - Content-Type: multipart/form-data
   - Body: username, password, scope (optional)
   - Returns: AccessToken with access_token (expires in 30 min), refresh_token (expires in 30 days)
   - Should validate credentials and return user info with tokens

2. POST /api/register
   - Content-Type: application/json
   - Body: { username, email, fullname, password }
   - Returns: User object (without password)
   - Validate: username 3+ chars, password 8+ chars, valid email format
   - Default: active=true, scopes=[] (empty array)

3. POST /api/refresh
   - Content-Type: application/json
   - Body: { refresh_token: string }
   - Returns: AccessToken with new access_token
   - Validate refresh_token from database and issue new access_token
   - Store tokens in database with expiry timestamps

4. GET /api/admin/scopes
   - Auth: Required (Bearer token)
   - Returns: string[] of available scopes
   - Example scopes: ["admin", "user", "guest"]

5. GET /api/admin/users
   - Auth: Required (admin scope)
   - Query params: skip (default: 0), limit (default: 100)
   - Returns: User[] array with pagination

6. GET /api/admin/users/{username}
   - Auth: Required (admin scope)
   - Returns: User object for specific username
   - 404 if not found

7. POST /api/admin/users
   - Auth: Required (admin scope)
   - Content-Type: application/json
   - Body: { username, password, email, fullname, active?, scopes? }
   - Returns: Created User object
   - Validate uniqueness of username and email

8. PUT /api/admin/users/{username}
   - Auth: Required (admin scope)
   - Content-Type: application/json
   - Body: { email?, fullname?, password?, active?, scopes? } (all optional)
   - Returns: Updated User object
   - Only update provided fields, hash password if provided

9. DELETE /api/admin/users/{username}
   - Auth: Required (admin scope)
   - Returns: { detail: "User deleted successfully" }
   - 404 if user not found
"""

from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
import re

from .manager import UserManager, TokenManager
from .middleware import get_db, get_current_active_user, get_admin_user
from .models import User, AccessToken, SCOPES


# Initialize router
router = APIRouter()

# Initialize managers
user_manager = UserManager()
token_manager = TokenManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3,
                          description="Username must be at least 3 characters")
    email: EmailStr
    fullname: str
    password: str = Field(..., min_length=8,
                          description="Password must be at least 8 characters")

    @field_validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty or whitespace only')
        return v.strip()

    @field_validator('fullname')
    def validate_fullname(cls, v):
        if not v.strip():
            raise ValueError('Fullname cannot be empty or whitespace only')
        return v.strip()


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    fullname: str
    password: str = Field(..., min_length=8)
    active: Optional[bool] = True
    scopes: Optional[List[str]] = []


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    fullname: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    active: Optional[bool] = None
    scopes: Optional[List[str]] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    fullname: str
    active: bool
    scopes: List[str]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    fullname: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/api/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access and refresh tokens.

    - **username**: User's username
    - **password**: User's password
    - **scope**: Optional scopes (space-separated)
    """
    # Authenticate user
    user = user_manager.authenticate_user(
        db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(seconds=token_manager.access_token_expire)
    access_token = token_manager.create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires
    )

    # Create and store refresh token
    refresh_token = token_manager.create_refresh_token()
    token_manager.store_refresh_token(db, refresh_token, user.id)

    # determine the role from scopes
    role = ''
    if 'admin' in user.scopes:
        role = 'admin'
    elif 'user' in user.scopes:
        role = 'user'
    else:
        role = 'guest'

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=token_manager.access_token_expire,
        fullname=user.fullname,
        email=user.email,
        role=role
    )


@router.post("/api/register", response_model=UserResponse, tags=["Authentication"])
async def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    - **username**: Unique username (min 3 characters)
    - **email**: Valid email address
    - **fullname**: User's full name
    - **password**: Password (min 8 characters)
    """
    # Check if username already exists
    existing_user = user_manager.get_user(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = user_manager.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = user_manager.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        fullname=user_data.fullname,
        password=user_data.password,
        active=True,
        scopes=[]
    )

    return UserResponse(**user.dict())


@router.post("/api/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token
    """
    # Validate refresh token
    db_token = token_manager.get_refresh_token(db, token_data.refresh_token)

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    from .database import UserDB
    db_user = db.query(UserDB).filter(UserDB.id == db_token.user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not db_user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create new access token
    access_token_expires = timedelta(seconds=token_manager.access_token_expire)
    access_token = token_manager.create_access_token(
        data={"sub": db_user.username, "scopes": db_user.scopes or []},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=token_data.refresh_token,
        token_type="bearer",
        expires_in=token_manager.access_token_expire,
        fullname=db_user.fullname,
        email=db_user.email,
        role='admin' if 'admin' in (db_user.scopes or []) else 'user' if 'user' in (db_user.scopes or []) else 'guest'
    )


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/api/admin/scopes", response_model=List[str], tags=["Admin"])
async def get_scopes(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available user scopes.
    Requires authentication.
    """
    return SCOPES


@router.get("/api/admin/users", response_model=List[UserResponse], tags=["Admin"])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get list of all users with pagination.
    Requires admin scope.

    - **skip**: Number of users to skip (default: 0)
    - **limit**: Maximum number of users to return (default: 100)
    """
    users = user_manager.get_users(db, skip=skip, limit=limit)
    return [UserResponse(**user.dict()) for user in users]


@router.get("/api/admin/users/{username}", response_model=UserResponse, tags=["Admin"])
async def get_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get user by username.
    Requires admin scope.

    - **username**: Username to retrieve
    """
    user = user_manager.get_user(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return UserResponse(**user.dict())


@router.post("/api/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Admin"])
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Create a new user.
    Requires admin scope.

    - **username**: Unique username (min 3 characters)
    - **email**: Valid email address
    - **fullname**: User's full name
    - **password**: Password (min 8 characters)
    - **active**: User active status (default: true)
    - **scopes**: User scopes (default: [])
    """
    # Check if username already exists
    existing_user = user_manager.get_user(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = user_manager.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create user
    user = user_manager.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        fullname=user_data.fullname,
        password=user_data.password,
        active=user_data.active,
        scopes=user_data.scopes
    )

    return UserResponse(**user.dict())


@router.put("/api/admin/users/{username}", response_model=UserResponse, tags=["Admin"])
async def update_user(
    username: str,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update user information.
    Requires admin scope.

    - **username**: Username to update
    - **email**: New email (optional)
    - **fullname**: New full name (optional)
    - **password**: New password (optional, min 8 characters)
    - **active**: New active status (optional)
    - **scopes**: New scopes (optional)
    """
    # Check if user exists
    existing_user = user_manager.get_user(db, username)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Check if email is being changed and already exists
    if user_data.email and user_data.email != existing_user.email:
        existing_email = user_manager.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    # Update user
    updated_user = user_manager.update_user(
        db=db,
        username=username,
        email=user_data.email,
        fullname=user_data.fullname,
        password=user_data.password,
        active=user_data.active,
        scopes=user_data.scopes
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

    return UserResponse(**updated_user.dict())


@router.delete("/api/admin/users/{username}", tags=["Admin"])
async def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a user.
    Requires admin scope.

    - **username**: Username to delete
    """
    # Check if user exists
    existing_user = user_manager.get_user(db, username)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Prevent deleting yourself
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Delete user
    success = user_manager.delete_user(db, username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

    return {"detail": "User deleted successfully"}
