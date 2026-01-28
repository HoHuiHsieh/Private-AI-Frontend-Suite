"""
Configuration data models
"""

from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field


@dataclass
class AuthenticationConfig:
    """OAuth2 configuration settings."""
    enable: bool
    secret_key: str
    algorithm: Literal['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
    access_token_expire_time: int
    refresh_token_expire_time: int
    default_admin: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate authentication configuration."""
        if self.enable:
            if not self.secret_key or len(self.secret_key) < 16:
                raise ValueError(
                    "oauth2.secret_key: Secret key must be at least 16 characters when authentication is enabled"
                )

        valid_algorithms = ['HS256', 'HS384',
                            'HS512', 'RS256', 'RS384', 'RS512']
        if self.algorithm not in valid_algorithms:
            raise ValueError(
                f"oauth2.algorithm: Algorithm must be one of: {', '.join(valid_algorithms)}"
            )

        if self.access_token_expire_time <= 0:
            raise ValueError(
                "oauth2.access_token_expire_time: Access token expiration time must be positive"
            )

        if self.refresh_token_expire_time <= 0:
            raise ValueError(
                "oauth2.refresh_token_expire_time: Refresh token expiration time must be positive"
            )

        if self.refresh_token_expire_time < self.access_token_expire_time:
            raise ValueError(
                "oauth2.refresh_token_expire_time: Refresh token expiration should be greater than or equal to access token expiration"
            )


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    username: str
    password: str
    database: str
    table_prefix: str = ""

    def __post_init__(self):
        """Validate database configuration."""
        if not self.host or not self.host.strip():
            raise ValueError("database.host: Database host is required")

        if not (1 <= self.port <= 65535):
            raise ValueError(
                f"database.port: Database port must be between 1 and 65535, got {self.port}"
            )

        if not self.username:
            raise ValueError(
                "database.username: Database username is required")

        if not self.password:
            raise ValueError(
                "database.password: Database password is required")

        if not self.database:
            raise ValueError("database.database: Database name is required")

    def db_connection_string(self, name=None) -> str:
        """Generate database connection string."""
        dbname = name if name else self.database
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{dbname}"

    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"



@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str
    database: Dict[str, Any] = field(default_factory=dict)
    console: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"logging.level: Log level must be one of: {', '.join(valid_levels)}"
            )

        # Normalize level to uppercase
        self.level = self.level.upper()

        # Validate database logging config
        if self.database.get('enabled'):
            retention_days = self.database.get('retention_days', 0)
            if retention_days < 0:
                raise ValueError(
                    "logging.database.retention_days: Retention days must be non-negative"
                )

        # Validate component log levels
        for component, level in self.components.items():
            if level.upper() not in valid_levels:
                raise ValueError(
                    f"logging.components.{component}: Component log level must be one of: {', '.join(valid_levels)}"
                )
            # Normalize component levels to uppercase
            self.components[component] = level.upper()


@dataclass
class ModelConfig:
    """Individual model configuration."""
    host: List[str]
    port: List[int]
    serve_type: List[str]
    source_type: Literal['openai:chat', 'openai:responses', 'openai:embeddings',
                         'openai:audio:transcription',
                         'triton:embeddings', 'triton:audio:transcription']
    response: Dict[str, Dict[str, str]]
    public_api_key: Optional[str]
    args: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate model configuration."""
        # Validate host list
        if not self.host or len(self.host) == 0:
            raise ValueError("model.host: Model host list cannot be empty")

        for i, host in enumerate(self.host):
            if not host or not host.strip():
                raise ValueError(
                    f"model.host[{i}]: Host at index {i} cannot be empty")

        # Validate port list
        if not self.port or len(self.port) == 0:
            raise ValueError("model.port: Model port list cannot be empty")

        for i, port in enumerate(self.port):
            if not (1 <= port <= 65535):
                raise ValueError(
                    f"model.port[{i}]: Port at index {i} must be between 1 and 65535, got {port}"
                )

        # Validate that host and port lists are compatible
        if len(self.host) > 1 and len(self.port) > 1 and len(self.host) != len(self.port):
            raise ValueError(
                f"model: Host and port lists must have the same length or one must have length 1. "
                f"Got {len(self.host)} hosts and {len(self.port)} ports"
            )

        # Validate serve_type
        if not self.serve_type or len(self.serve_type) == 0:
            raise ValueError(
                "model.serve_type: Model must have at least one serve type")

        # Validate source_type
        valid_source_types = ['openai:chat', 'openai:responses', 'openai:embeddings',
                              'openai:audio:transcription',
                              'triton:embeddings', 'triton:audio:transcription']
        if self.source_type not in valid_source_types:
            raise ValueError(
                f"model.source_type ({self.source_type}): Source type must be one of: {', '.join(valid_source_types)}"
            )

    @property
    def endpoint(self) -> str:
        """Get the full endpoint URL. Returns the first endpoint if multiple are configured."""
        if self.host and self.port:
            return f"{self.host[0]}:{self.port[0]}"
        return ""

    @property
    def endpoints(self) -> List[str]:
        """Get all endpoint URLs."""
        if not self.host or not self.port:
            return []

        # If lengths don't match, pair each host with the first port
        if len(self.host) != len(self.port):
            port = self.port[0] if self.port else 8000
            return [f"{h}:{port}" for h in self.host]

        return [f"{h}:{p}" for h, p in zip(self.host, self.port)]
