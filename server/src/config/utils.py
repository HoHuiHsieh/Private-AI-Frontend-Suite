"""
Global configuration instance and utilities
"""

from typing import Optional
from .manager import Config

# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(
    dotenv_path: Optional[str] = None
) -> Config:
    """
    Get the global configuration instance.
    
    Creates a new instance on first call with the provided parameters.
    Subsequent calls return the existing instance and ignore parameters.
    
    Args:
        dotenv_path: Path to .env file (only used on first call)
    
    Returns:
        Config instance
        
    Raises:
        ValueError: If configuration validation fails
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(dotenv_path=dotenv_path)
    
    return _config_instance


def reload_config() -> None:
    """
    Reload the global configuration from environment variables and .env file.
    
    Raises:
        RuntimeError: If config has not been initialized yet
    """
    global _config_instance
    
    if _config_instance is None:
        raise RuntimeError("Configuration not initialized. Call get_config() first.")
    
    _config_instance.reload()


def reset_config() -> None:
    """
    Reset the global configuration instance.
    
    Useful for testing or forcing reinitialization with different parameters.
    """
    global _config_instance
    _config_instance = None


def is_config_initialized() -> bool:
    """
    Check if the global configuration has been initialized.
    
    Returns:
        True if config instance exists, False otherwise
    """
    return _config_instance is not None
