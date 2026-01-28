"""
API Key Manager

Handles API key generation, validation, and CRUD operations.
"""

import secrets
import string
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from .database import ApiKeyDB
from .models import ApiKey


class ApiKeyManager:
    """Manager for API key operations."""
    
    # API key configuration
    API_KEY_PREFIX = "sk-"
    API_KEY_LENGTH = 48
    
    def __init__(self):
        """Initialize API key manager."""
        pass
    
    def generate_api_key(self) -> str:
        """
        Generate a cryptographically secure API key.
        
        Returns:
            String in format: sk-<48_random_characters>
        """
        # Use alphanumeric characters for the key
        alphabet = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(self.API_KEY_LENGTH))
        return f"{self.API_KEY_PREFIX}{random_part}"
    
    def create_api_key(
        self,
        db: Session,
        user_id: int,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> ApiKey:
        """
        Create a new API key for a user.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the key
            name: Optional name/label for the key
            expires_at: Optional expiration datetime
        
        Returns:
            ApiKey object with the full API key value
        """
        # Generate unique API key (retry if collision)
        max_retries = 5
        for _ in range(max_retries):
            api_key = self.generate_api_key()
            existing = db.query(ApiKeyDB).filter(ApiKeyDB.api_key == api_key).first()
            if not existing:
                break
        else:
            raise RuntimeError("Failed to generate unique API key after multiple attempts")
        
        # Create database entry
        db_api_key = ApiKeyDB(
            api_key=api_key,
            user_id=user_id,
            name=name,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        
        return self._db_apikey_to_model(db_api_key)
    
    def get_api_keys(
        self,
        db: Session,
        user_id: int,
        include_revoked: bool = True
    ) -> List[ApiKey]:
        """
        Get all API keys for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            include_revoked: If False, only return active keys
        
        Returns:
            List of ApiKey objects, sorted by created_at descending
        """
        query = db.query(ApiKeyDB).filter(ApiKeyDB.user_id == user_id)
        
        if not include_revoked:
            query = query.filter(ApiKeyDB.revoked == False)
        
        db_keys = query.order_by(ApiKeyDB.created_at.desc()).all()
        return [self._db_apikey_to_model(key) for key in db_keys]
    
    def get_api_key_by_id(
        self,
        db: Session,
        key_id: int,
        user_id: Optional[int] = None
    ) -> Optional[ApiKey]:
        """
        Get an API key by its ID.
        
        Args:
            db: Database session
            key_id: ID of the API key
            user_id: Optional user ID to filter by ownership
        
        Returns:
            ApiKey object or None if not found
        """
        query = db.query(ApiKeyDB).filter(ApiKeyDB.id == key_id)
        
        if user_id is not None:
            query = query.filter(ApiKeyDB.user_id == user_id)
        
        db_key = query.first()
        if db_key:
            return self._db_apikey_to_model(db_key)
        return None
    
    def get_api_key_by_key(self, db: Session, api_key: str) -> Optional[ApiKey]:
        """
        Get an API key by its key value.
        
        Args:
            db: Database session
            api_key: The API key string
        
        Returns:
            ApiKey object or None if not found
        """
        db_key = db.query(ApiKeyDB).filter(ApiKeyDB.api_key == api_key).first()
        if db_key:
            return self._db_apikey_to_model(db_key)
        return None
    
    def revoke_api_key(
        self,
        db: Session,
        key_id: int,
        user_id: int
    ) -> bool:
        """
        Revoke an API key.
        
        Args:
            db: Database session
            key_id: ID of the API key to revoke
            user_id: ID of the user (for ownership verification)
        
        Returns:
            True if successfully revoked, False if not found or doesn't belong to user
        """
        db_key = db.query(ApiKeyDB).filter(
            ApiKeyDB.id == key_id,
            ApiKeyDB.user_id == user_id
        ).first()
        
        if not db_key:
            return False
        
        db_key.revoked = True
        db.commit()
        return True
    
    def validate_api_key(
        self,
        db: Session,
        api_key: str
    ) -> Optional[ApiKey]:
        """
        Validate an API key and return it if valid.
        
        An API key is valid if:
        - It exists in the database
        - It is not revoked
        - It is not expired
        
        Args:
            db: Database session
            api_key: The API key string to validate
        
        Returns:
            ApiKey object if valid, None otherwise
        """
        db_key = db.query(ApiKeyDB).filter(ApiKeyDB.api_key == api_key).first()
        
        if not db_key:
            return None
        
        # Check if revoked
        if db_key.revoked:
            return None
        
        # Check if expired
        if db_key.expires_at:
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Make expires_at timezone-aware if it's naive
            expires_at = db_key.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < now:
                return None
        
        return self._db_apikey_to_model(db_key)
    
    def _db_apikey_to_model(self, db_key: ApiKeyDB) -> ApiKey:
        """Convert database API key to model API key."""
        return ApiKey(
            id=db_key.id,
            api_key=db_key.api_key,
            user_id=db_key.user_id,
            name=db_key.name,
            expires_at=db_key.expires_at,
            revoked=db_key.revoked,
            created_at=db_key.created_at
        )
