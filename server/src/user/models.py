"""
User data models
"""

from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from datetime import datetime


SCOPES = ["admin", "user", "guest"]


@dataclass
class User:
    """User data model."""
    username: str
    email: str
    fullname: str
    active: bool = True
    scopes: List[str] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        data = {
            "username": self.username,
            "email": self.email,
            "fullname": self.fullname,
            "active": self.active,
            "scopes": self.scopes,
        }
        if self.id is not None:
            data["id"] = self.id
        if self.created_at is not None:
            data["created_at"] = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        if self.updated_at is not None:
            data["updated_at"] = self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
            
        if exclude:
            for key in exclude:
                data.pop(key, None)
        return data


@dataclass
class AccessToken:
    """Access token data model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert token to dictionary representation."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
        }
        if self.expires_in is not None:
            data["expires_in"] = self.expires_in
        return data


@dataclass
class TokenData:
    """Token payload data model."""
    sub: str  # username
    scopes: List[str] = field(default_factory=list)
    exp: Optional[int] = None
    iat: Optional[int] = None

