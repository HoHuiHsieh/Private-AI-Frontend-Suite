"""
User Module

This module handles user management, including authentication and authorization
using OAuth2 protocol for webui.

Module Structure:
- __init__.py:                 This file initializes the module
- manager.py:                  User and token management logic
- models.py:                   User and token data models
- database.py:                 Database setup and token model
- middleware.py:               Middleware for user information extraction from access token
- route.py:                    API route definitions

Usage:
    from user import router, UserManager, TokenManager
    from user import User, AccessToken, TokenData
    from user import get_current_user, get_current_active_user, get_admin_user
"""

# Import managers
from .manager import UserManager, TokenManager

# Import models
from .models import User, AccessToken, TokenData, SCOPES

# Import middleware dependencies
from .middleware import (
    get_db,
    get_current_user,
    get_current_active_user,
    get_admin_user,
)

# Import router
from .route import router

# Import database models and utilities
from .database import (
    UserDB,
    RefreshTokenDB,
)


__all__ = [
    # Router
    'router',
    
    # Managers
    'UserManager',
    'TokenManager',
    
    # Data Models
    'User',
    'AccessToken',
    'TokenData',
    'SCOPES',
    
    # Middleware
    'get_db',
    'get_current_user',
    'get_current_active_user',
    'get_admin_user',
    
    # Database
    'UserDB',
    'RefreshTokenDB',
]