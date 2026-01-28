"""
API Key Module

This module handles API key management for the application.

Module Structure:
- __init__.py:      This file initializes the module
- manager.py:       API key generation and management logic
- models.py:        API key data models
- database.py:      Database setup and API key model
- middleware.py:    Middleware for API key authentication
- route.py:         API route definitions

Usage:
    from apikey import router, ApiKeyManager
    from apikey import ApiKey, ApiKeyCreate
    from apikey import get_current_user_from_api_key
"""

# Import manager
from .manager import ApiKeyManager

# Import models
from .models import ApiKey, ApiKeyCreate

# Import middleware
from .middleware import (
    get_current_user_from_api_key,
    validate_api_key_header,
)

# Import router
from .route import router



__all__ = [
    # Router
    'router',
    
    # Manager
    'ApiKeyManager',
    
    # Data Models
    'ApiKey',
    'ApiKeyCreate',
    
    # Middleware
    'get_current_user_from_api_key',
    'validate_api_key_header',
]