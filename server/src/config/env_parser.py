"""
Type-safe environment variable parser
"""

import os
from typing import Optional, List, Any


class EnvParser:
    """Helper class for parsing environment variables with type safety."""
    
    @staticmethod
    def get_str(key: str, default: str = "") -> str:
        """Get string value from environment variable."""
        return os.getenv(key, default)
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """
        Get boolean value from environment variable.
        
        Accepts: true/false, 1/0, yes/no, on/off (case-insensitive)
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_list(key: str, default: Optional[List[str]] = None, separator: str = ',') -> List[str]:
        """
        Get list value from environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            separator: Separator character (default: comma)
        
        Returns:
            List of strings
        """
        if default is None:
            default = []
        
        value = os.getenv(key)
        if value is None:
            return default
        
        # Split and strip whitespace from each item
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @staticmethod
    def get_dict(key_prefix: str, fields: List[str]) -> dict:
        """
        Get dictionary from environment variables with a common prefix.
        
        Args:
            key_prefix: Prefix for environment variables (e.g., 'DEFAULT_ADMIN_')
            fields: List of field names to look for
        
        Returns:
            Dictionary with found values
        """
        result = {}
        for field in fields:
            env_key = f"{key_prefix}{field.upper()}"
            value = os.getenv(env_key)
            if value is not None:
                result[field.lower()] = value
        return result
    
    @staticmethod
    def has_key(key: str) -> bool:
        """Check if environment variable exists."""
        return key in os.environ
    
    @staticmethod
    def get_or_raise(key: str, error_message: Optional[str] = None) -> str:
        """
        Get environment variable or raise error if not found.
        
        Args:
            key: Environment variable name
            error_message: Custom error message
        
        Raises:
            KeyError: If environment variable is not found
        """
        value = os.getenv(key)
        if value is None:
            msg = error_message or f"Required environment variable '{key}' is not set"
            raise KeyError(msg)
        return value
