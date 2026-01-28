"""
Configuration loader and parser with environment variable support
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import AuthenticationConfig, DatabaseConfig, LoggingConfig, ModelConfig
from .env_parser import EnvParser


class EnvConfigLoader:
    """Handles loading and parsing configuration from environment variables."""

    @staticmethod
    def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
        """
        Load environment variables from .env file.

        Args:
            dotenv_path: Path to .env file. If None, looks for .env in common locations.
        """
        try:
            from dotenv import load_dotenv

            if dotenv_path and dotenv_path.exists():
                load_dotenv(dotenv_path, override=False)
            else:
                # Try to find .env in common locations
                load_dotenv(override=False)
        except ImportError:
            # python-dotenv not installed, skip
            pass

    @staticmethod
    def parse_authentication_config() -> AuthenticationConfig:
        """
        Parse authentication configuration from environment variables.

        Priority: Environment variables > .env file > defaults

        Returns:
            AuthenticationConfig object
        """
        # Parse enable flag
        enable = EnvParser.get_bool('OAUTH2_ENABLE', True)

        # Parse default admin from environment variables
        default_admin = {}

        # Check if any DEFAULT_ADMIN_ environment variables exist
        if EnvParser.has_key('DEFAULT_ADMIN_USERNAME'):
            # Parse all admin fields
            username = EnvParser.get_str('DEFAULT_ADMIN_USERNAME', '')
            email = EnvParser.get_str('DEFAULT_ADMIN_EMAIL', '')
            full_name = EnvParser.get_str('DEFAULT_ADMIN_FULL_NAME', '')
            password = EnvParser.get_str('DEFAULT_ADMIN_PASSWORD', '')
            disabled = EnvParser.get_bool('DEFAULT_ADMIN_DISABLED', False)

            # Only set default_admin if we have at least username and password
            if username and password:
                default_admin = {
                    'username': username,
                    'email': email,
                    'full_name': full_name,
                    'password': password,
                    'disabled': disabled
                }

        return AuthenticationConfig(
            enable=enable,
            secret_key=EnvParser.get_str('OAUTH2_SECRET_KEY', ''),
            algorithm=EnvParser.get_str('OAUTH2_ALGORITHM', 'HS256'),
            access_token_expire_time=EnvParser.get_int(
                'OAUTH2_ACCESS_TOKEN_EXPIRE_TIME', 3600),
            refresh_token_expire_time=EnvParser.get_int(
                'OAUTH2_REFRESH_TOKEN_EXPIRE_TIME', 2592000),
            default_admin=default_admin
        )

    @staticmethod
    def parse_database_config() -> DatabaseConfig:
        """
        Parse database configuration from environment variables.

        Priority: Environment variables > .env file > defaults

        Returns:
            DatabaseConfig object
        """
        return DatabaseConfig(
            host=EnvParser.get_str('DATABASE_HOST', 'localhost'),
            port=EnvParser.get_int('DATABASE_PORT', 5432),
            username=EnvParser.get_str('DATABASE_USERNAME', ''),
            password=EnvParser.get_str('DATABASE_PASSWORD', ''),
            database=EnvParser.get_str('DATABASE_NAME', ''),
            table_prefix=EnvParser.get_str('DATABASE_TABLE_PREFIX', '')
        )

    @staticmethod
    def parse_logging_config() -> LoggingConfig:
        """
        Parse logging configuration from environment variables.

        Priority: Environment variables > .env file > defaults

        Returns:
            LoggingConfig object
        """
        # Parse database logging config
        database_config = {
            'enabled': EnvParser.get_bool('LOGGING_DATABASE_ENABLED', False),
            'retention_days': EnvParser.get_int('LOGGING_DATABASE_RETENTION_DAYS', 365)
        }

        # Parse console logging config
        console_config = {
            'enabled': EnvParser.get_bool('LOGGING_CONSOLE_ENABLED', True),
            'format': EnvParser.get_str('LOGGING_CONSOLE_FORMAT',
                                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }

        return LoggingConfig(
            level=EnvParser.get_str('LOGGING_LEVEL', 'INFO'),
            database=database_config,
            console=console_config,
            components={}
        )


class YmlConfigLoader:

    @staticmethod
    def load_yml_file(file_path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.

        Args:
            file_path (str): Path to the YAML file.

        Returns:
            Dict[str, Any]: Parsed YAML data.
        """
        import yaml
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading YAML file: {e}")
            return {}

    @staticmethod
    def parse_models_config(filepath: Path) -> Dict[str, ModelConfig]:
        """
        Parse models configuration from YAML file.

        Args:
            filepath: Path to the YAML file containing model configurations

        Returns:
            Dictionary of model name to ModelConfig
        """
        models = {}

        # Load models from yml file
        yml_data = YmlConfigLoader.load_yml_file(filepath)

        if not yml_data or 'models' not in yml_data:
            return models

        yml_models = yml_data.get('models', {})

        for model_name, yml_model_data in yml_models.items():
            # Create model from yml data
            models[model_name] = YmlConfigLoader._create_model_from_yml(
                yml_model_data)

        return models

    @staticmethod
    def _create_model_from_yml(yml_data: Dict[str, Any]) -> ModelConfig:
        """
        Create ModelConfig from YAML data.

        Args:
            yml_data: Dictionary containing model configuration from YAML

        Returns:
            ModelConfig object
        """
        # Parse serve_type field (e.g., ["openai:chat", "openai:response"])
        serve_type = yml_data.get('serve_type', [])
        if isinstance(serve_type, str):
            serve_type_list = [serve_type] if serve_type else []
        elif isinstance(serve_type, list):
            serve_type_list = serve_type
        else:
            serve_type_list = []

        # Parse public_api_key field
        public_api_key = yml_data.get('public_api_key', '')

        # Parse source_type field (e.g., "openai:responses", "triton:embeddings")
        source_type = yml_data.get('source_type', '')

        # Parse host - should be a list
        host_data = yml_data.get('host', [])
        if isinstance(host_data, str):
            host = [host_data]
        elif isinstance(host_data, list):
            host = host_data
        else:
            host = []

        # Parse port - should be a list matching host length
        port_data = yml_data.get('port', [])
        if isinstance(port_data, int):
            port = [port_data]
        elif isinstance(port_data, list):
            port = port_data
        elif isinstance(port_data, str):
            port = [int(port_data)]
        else:
            port = [8000]  # Default port

        # Parse response data if present
        response = yml_data.get('response', {})
        if response and isinstance(response, dict):
            # Ensure all required fields are present
            response_data = {
                'id': response.get('id', ''),
                'created': response.get('created', 0),
                'object': response.get('object', 'model'),
                'owned_by': response.get('owned_by', '')
            }
        else:
            response_data = {}

        # Parse args if present
        args = yml_data.get('args', None)
        if args and not isinstance(args, dict):
            args = None

        return ModelConfig(
            host=host,
            port=port,
            serve_type=serve_type_list,
            source_type=source_type,
            args=args,
            response=response_data,
            public_api_key=public_api_key
        )

    @staticmethod
    def parse_collitions_config(filepath: Path) -> List[str]:
        """
        Parse collections configuration from YAML file.
        """
        collections = []

        # Load collections from yml file
        yml_data = YmlConfigLoader.load_yml_file(filepath)

        if not yml_data or 'collections' not in yml_data:
            return collections

        yml_collections = yml_data.get('collections', [])

        for collection_name in yml_collections:
            collections.append(collection_name)

        return collections
