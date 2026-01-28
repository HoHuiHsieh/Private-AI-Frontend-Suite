"""
API Key Management Routes

ENDPOINTS:

1. GET /api/apikeys
   - Auth: Required (Bearer token)
   - Returns: ApiKey[] array for the authenticated user
   - Filter: Only return keys belonging to the authenticated user
   - Include: All fields including revoked status
   - Sort: By created_at descending (newest first)

2. POST /api/apikeys
   - Auth: Required (Bearer token)
   - Content-Type: application/json
   - Body: { name: string, days: int } (both required)
   - Returns: ApiKey object with the FULL api_key value
   - Generate: Secure random API key with "sk-" prefix (e.g., "sk-" + 48 random characters)
   - Set: user_id from authenticated user
   - Set: revoked = false
   - Set: created_at = current timestamp
   - Set: expires_at = current timestamp + days
   - IMPORTANT: Return the full API key only on creation - this is the only time the user can see it

3. POST /api/apikeys/{keyId}/revoke
   - Auth: Required (Bearer token)
   - Returns: { detail: "API key revoked successfully" }
   - Validate: Key belongs to authenticated user
   - Action: Set revoked = true
   - 404 if key not found or doesn't belong to user
   - 400 if key is already revoked
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from user import get_current_active_user, get_db, User
from .manager import ApiKeyManager
from .models import ApiKey


# Initialize router
router = APIRouter()

# Initialize manager
apikey_manager = ApiKeyManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class ApiKeyCreateRequest(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Name/label for the key (required)")
    days: int = Field(..., gt=0, description="Number of days until expiration (required, must be positive)")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class ApiKeyResponse(BaseModel):
    """Response model for API key."""
    id: int
    api_key: str
    user_id: int
    name: Optional[str] = None
    expires_at: Optional[str] = None
    revoked: bool
    created_at: str
    
    class Config:
        from_attributes = True


# ============================================================================
# API Key Endpoints
# ============================================================================

@router.get("/api/apikeys", response_model=List[ApiKeyResponse], tags=["API Keys"])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all API keys for the authenticated user.
    
    Returns list of API keys sorted by creation date (newest first).
    API keys are masked for security (only showing prefix and last 4 characters).
    """
    keys = apikey_manager.get_api_keys(db, user_id=current_user.id, include_revoked=True)
    
    # Return masked API keys (not showing full key for security)
    return [ApiKeyResponse(**key.dict(show_api_key=False)) for key in keys]


@router.post("/api/apikeys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED, tags=["API Keys"])
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the authenticated user.
    
    **IMPORTANT**: The full API key is only returned on creation. 
    Save it securely as you won't be able to see it again.
    
    - **name**: Label for the key (required, max 100 characters)
    - **days**: Number of days until expiration (required, must be positive)
    """
    try:
        # Calculate expiration date from days
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.days)
        
        api_key = apikey_manager.create_api_key(
            db=db,
            user_id=current_user.id,
            name=request.name,
            expires_at=expires_at
        )
        
        # Return the FULL API key only on creation
        return ApiKeyResponse(**api_key.dict(show_api_key=True))
    
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/api/apikeys/{key_id}/revoke", tags=["API Keys"])
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    
    Once revoked, the API key can no longer be used for authentication.
    
    - **key_id**: ID of the API key to revoke
    """
    # Check if key exists and belongs to user
    existing_key = apikey_manager.get_api_key_by_id(db, key_id, user_id=current_user.id)
    
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {key_id} not found or does not belong to you"
        )
    
    # Check if already revoked
    if existing_key.revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )
    
    # Revoke the key
    success = apikey_manager.revoke_api_key(db, key_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )
    
    return {"detail": "API key revoked successfully"}
