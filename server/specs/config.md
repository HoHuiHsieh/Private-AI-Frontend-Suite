# Module: config

## 1. Purpose
The config module provides a robust way to load, parse, validate, and access configuration settings from environment variables and .yml files.

## 2. Requirements
- Environment variable support with type safety
- .yml file loading with model configurations
- Automatic configuration validation via dataclass __post_init__
- Support for authentication, database, logging, and model configurations
- Priority: Environment variables > .env file > defaults
- Invalid configurations raise ValueError with descriptive messages

## 3. Design
- Main components: Config manager class, get_config() function, reload_config(), reset_config(), is_config_initialized()
- Configuration data models: AuthenticationConfig, DatabaseConfig, LoggingConfig, ModelConfig
- Uses dataclasses for validation
- Centralized configuration management