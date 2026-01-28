"""
Configuration module for application settings management.

This module provides a robust way to load, parse, validate, and access configuration
settings from environment variables and .yml files.

Features:
- Environment variable support with type safety
- .yml file loading with model configurations
- Automatic configuration validation via dataclass __post_init__
- Support for authentication, database, logging, and model configurations

Main components:
- Config: Main configuration manager class
- get_config(): Get global configuration instance
- reload_config(): Reload configuration from environment
- reset_config(): Reset the global configuration instance
- is_config_initialized(): Check if configuration has been initialized
- Configuration data models for different settings sections

Priority: Environment variables > .env file > defaults

Validation:
All configuration models automatically validate on instantiation using __post_init__.
Invalid configurations will raise ValueError with descriptive error messages.
"""

from .manager import Config
from .models import (
    AuthenticationConfig,
    DatabaseConfig, 
    LoggingConfig,
    ModelConfig
)
from .utils import get_config, reload_config, reset_config, is_config_initialized


__all__ = [
    'Config',
    'AuthenticationConfig',
    'DatabaseConfig',
    'LoggingConfig', 
    'ModelConfig',
    'get_config',
    'reload_config',
    'reset_config',
    'is_config_initialized',
]
