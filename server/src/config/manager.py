"""
Configuration manager class with validation and environment variable support
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from .models import AuthenticationConfig, DatabaseConfig, LoggingConfig, ModelConfig
from .loader import EnvConfigLoader, YmlConfigLoader


logger = logging.getLogger(__name__)


class Config:
    """
    Configuration class that loads and manages application settings.
    """

    DEFAULT_YML_FILEPATH = Path("/workspace/model.yml")

    def __init__(self, dotenv_path: Optional[str] = None):
        """
        Initialize configuration by loading from environment variables and .env file.

        Args:
            dotenv_path: Path to .env file. If None, searches common locations.
        """
        self._dotenv_path = Path(dotenv_path) if dotenv_path else None
        self._authentication: AuthenticationConfig
        self._database: DatabaseConfig
        self._logging: LoggingConfig
        self._models: Dict[str, ModelConfig] = {}
        self._collections: List[str] = []

        self.load()

    def load(self) -> None:
        """
        Load configuration from environment variables and .env file.

        Order of precedence:
        1. Environment variables (highest priority)
        2. .env file
        3. Defaults (lowest priority)
        """
        # Load .env file first (so OS env vars can override it)
        EnvConfigLoader.load_dotenv(self._dotenv_path)
        logger.info("Loaded configuration from environment variables")

        # Parse configuration sections
        self._parse_config()

    def reload(self) -> None:
        """Reload configuration from environment variables and .env file."""
        logger.info("Reloading configuration...")
        self.load()

    def _parse_config(self) -> None:
        """Parse configuration from environment variables into structured objects."""
        self._authentication = EnvConfigLoader.parse_authentication_config()
        self._database = EnvConfigLoader.parse_database_config()
        self._logging = EnvConfigLoader.parse_logging_config()
        self._models = YmlConfigLoader.parse_models_config(
            self.DEFAULT_YML_FILEPATH)
        self._collections = YmlConfigLoader.parse_collitions_config(
            self.DEFAULT_YML_FILEPATH)

    def get_authentication_config(self) -> AuthenticationConfig:
        """Get the authentication configuration."""
        return self._authentication

    def get_database_config(self) -> DatabaseConfig:
        """Get the database configuration."""
        return self._database

    def get_logging_config(self) -> LoggingConfig:
        """Get the logging configuration."""
        return self._logging

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get the configuration for a specific model."""
        return self._models.get(model_name)

    def get_model_response(self) -> List[Dict[str, Any]]:
        """Get the responses of the models."""
        return [model.response for model in self._models.values() if model.response]

    def get_collections(self) -> List[str]:
        """Get the list of collections."""
        return self._collections

    # Logging helper methods
    def get_logging_level(self) -> str:
        """Get the logging level."""
        return self._logging.level if self._logging else "INFO"

    def is_console_logging_enabled(self) -> bool:
        """Check if console logging is enabled."""
        if not self._logging or not self._logging.console:
            return True
        return self._logging.console.get('enabled', True)

    def is_database_logging_enabled(self) -> bool:
        """Check if database logging is enabled."""
        if not self._logging or not self._logging.database:
            return False
        return self._logging.database.get('enabled', False)

    def get_database_logging_retention_days(self) -> int:
        """Get the retention days for database logging."""
        if not self._logging or not self._logging.database:
            return 365  # Default
        return self._logging.database.get('retention_days', 365)

    def get_component_logging_level(self, component: str) -> str:
        """Get the logging level for a specific component."""
        if self._logging and self._logging.components and component in self._logging.components:
            return self._logging.components[component]
        return self.get_logging_level()
