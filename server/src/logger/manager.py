# -*- coding: utf-8 -*-
"""
Logger manager module.

Contains the LoggerManager class that handles centralized logging configuration
and management for the application.
"""

import logging
import sys
import threading
import atexit
from typing import Dict, Any, Optional
from pathlib import Path

from config import get_config
from .handlers import create_console_handler, create_database_handler


class LoggerManager:
    """
    Centralized logger manager that handles configuration and setup of all loggers.

    Features:
    - Automatic configuration from config file
    - Multiple handler support (console, database, file)
    - Component-specific log levels
    - Thread-safe operations
    - Graceful shutdown handling
    """

    def __init__(self, config=None):
        """
        Initialize the logger manager.

        Args:
            config: Configuration object. If None, will try to load from util module.
        """
        self.config = config
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._initialized = False
        self._is_shutting_down = False
        self._lock = threading.RLock()
        self._cleanup_thread = None

        # Default log format
        self.default_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"

        # Load configuration if not provided
        if self.config is None:
            self._load_config()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def _load_config(self):
        """Load configuration from the util module."""
        try:
            import sys
            import os
            # Add the src directory to path if not already there
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            self.config = get_config()

        except (ImportError, Exception) as e:
            print(
                f"Warning: Could not load configuration: {e}", file=sys.stderr)
            self.config = None

    def initialize(self) -> bool:
        """
        Initialize the logging system.

        Returns:
            bool: True if initialization successful
        """
        with self._lock:
            if self._initialized:
                return True

            try:
                # Set up root logger
                self._setup_root_logger()

                # Set up component loggers if configuration is available
                if self.config:
                    self._setup_component_loggers()

                # Clean up old logs if database logging is enabled
                if self.config and self.config.is_database_logging_enabled():
                    self.cleanup_old_logs()
                    self._start_periodic_cleanup()

                self._initialized = True
                return True

            except Exception as e:
                print(
                    f"Failed to initialize logging system: {e}", file=sys.stderr)
                return False

    def _setup_root_logger(self):
        """Set up the root logger with basic configuration."""
        root_logger = logging.getLogger()

        # Clear existing handlers
        root_logger.handlers.clear()

        # Set root level
        if self.config:
            level_str = self.config.get_logging_level()
            root_logger.setLevel(
                getattr(logging, level_str.upper(), logging.INFO))
        else:
            root_logger.setLevel(logging.INFO)

        # Add console handler if enabled
        if not self.config or self.config.is_console_logging_enabled():
            console_handler = create_console_handler(self.config)
            if console_handler:
                root_logger.addHandler(console_handler)
                self._handlers['console'] = console_handler

        # Add database handler if enabled and configured
        if self.config and self.config.is_database_logging_enabled():
            db_handler = create_database_handler(self.config)
            if db_handler:
                root_logger.addHandler(db_handler)
                self._handlers['database'] = db_handler

    def _setup_component_loggers(self):
        """Set up component-specific loggers with individual log levels."""
        if not self.config or not hasattr(self.config, 'logging') or not self.config.logging:
            return

        # Get component configurations
        components = getattr(self.config.logging, 'components', {})

        for component, level_str in components.items():
            # Create logger directly without using get_logger to avoid circular dependency
            logger = logging.getLogger(component)
            try:
                level = getattr(logging, level_str.upper(), logging.INFO)
                logger.setLevel(level)
                # Store in our cache
                self._loggers[component] = logger
            except AttributeError:
                print(
                    f"Warning: Invalid log level '{level_str}' for component '{component}'", file=sys.stderr)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.

        Args:
            name: Logger name

        Returns:
            Configured logger instance
        """
        with self._lock:
            # Allow getting loggers even during initialization
            if name in self._loggers:
                return self._loggers[name]

            logger = logging.getLogger(name)

            # Set component-specific level if configured and initialized
            if self.config and self._initialized:
                component_level = self.config.get_component_logging_level(name)
                try:
                    level = getattr(
                        logging, component_level.upper(), logging.INFO)
                    logger.setLevel(level)
                except AttributeError:
                    pass

            # Allow propagation to root logger
            logger.propagate = True

            self._loggers[name] = logger
            return logger

    def cleanup_old_logs(self):
        """
        Clean up old log entries based on retention policy.

        This method deletes log entries older than the configured retention days
        from the database if database logging is enabled and retention_days > 0.
        """
        if not self.config or not self.config.is_database_logging_enabled():
            return

        retention_days = self.config.get_database_logging_retention_days()
        if retention_days <= 0:
            return

        try:
            from database import get_db_session
            from database.schema import LogDB
            from datetime import datetime, timedelta, timezone

            cutoff_date = datetime.now(
                timezone.utc) - timedelta(days=retention_days)

            with get_db_session() as session:
                # Delete old log entries
                deleted_count = session.query(LogDB).filter(
                    LogDB.timestamp < cutoff_date
                ).delete()

                if deleted_count > 0:
                    logger = self.get_logger(__name__)
                    logger.info(
                        f"Cleaned up {deleted_count} old log entries (retention: {retention_days} days)")

        except Exception as e:
            print(f"Failed to cleanup old logs: {e}", file=sys.stderr)

    def _start_periodic_cleanup(self):
        """
        Start a background thread for periodic cleanup of old logs.

        Runs cleanup every 24 hours (86400 seconds).
        """
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def cleanup_worker():
            import time
            while not self._is_shutting_down:
                try:
                    # Sleep for 24 hours
                    time.sleep(86400)
                    if not self._is_shutting_down:
                        self.cleanup_old_logs()
                except Exception as e:
                    print(
                        f"Error in periodic log cleanup: {e}", file=sys.stderr)
                    break

        self._cleanup_thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,
            name="LogCleanupWorker"
        )
        self._cleanup_thread.start()

    def shutdown(self):
        """Shutdown the logging system gracefully."""
        with self._lock:
            if self._is_shutting_down:
                return

            self._is_shutting_down = True

            # Close all handlers
            for handler in self._handlers.values():
                try:
                    handler.close()
                except Exception as e:
                    print(f"Error closing handler: {e}", file=sys.stderr)

            self._handlers.clear()
            self._loggers.clear()
            self._initialized = False
