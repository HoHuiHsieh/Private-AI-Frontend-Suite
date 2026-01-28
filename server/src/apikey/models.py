"""
API Key data models
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ApiKey:
    """API key data model."""
    id: int
    api_key: str
    user_id: int
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
    revoked: bool = False
    created_at: Optional[datetime] = None
    
    def dict(self, show_api_key: bool = False) -> dict:
        """
        Convert API key to dictionary representation.
        
        Args:
            show_api_key: If True, includes the full API key. 
                         If False, masks it for security.
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if show_api_key:
            data["api_key"] = self.api_key
        else:
            # Mask the API key, showing only prefix and last 4 characters
            if len(self.api_key) > 8:
                data["api_key"] = f"{self.api_key[:6]}...{self.api_key[-4:]}"
            else:
                data["api_key"] = "sk-****"
        
        return data


@dataclass
class ApiKeyCreate:
    """API key creation request model."""
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
