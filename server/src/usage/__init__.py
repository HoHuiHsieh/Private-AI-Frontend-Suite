# -*- coding: utf-8 -*-
"""
Usage Module

This module handles usage tracking and analytics for the application.

Module Structure:
- __init__.py:      This file initializes the module
- manager.py:       Usage tracking and analytics logic
- models.py:        Usage data models
- database.py:      Database setup and usage model
- route.py:         API route definitions
- utils.py:         Utility functions for logging usage

Usage:
    from usage import router, UsageManager
    from usage import UsageRecord, UsageOverview, SystemOverview
    from usage import get_gpu_status
    from usage import log_openai_usage, log_usage
"""

# Import manager
from .manager import UsageManager, get_gpu_status

# Import models
from .models import (
    UsageRecord,
    DailyUsage,
    UsageOverview,
    ModelUsage,
    SystemOverview,
    GPUStatus
)

# Import router
from .route import router

# Import database utilities
from .database import (
    get_database_session,
    init_database
)

# Import usage logging utilities
from .utils import (
    log_openai_usage,
    log_usage,
    async_log_openai_usage,
    async_log_usage
)


__all__ = [
    # Router
    'router',
    
    # Manager
    'UsageManager',
    'get_gpu_status',
    
    # Data Models
    'UsageRecord',
    'DailyUsage',
    'UsageOverview',
    'ModelUsage',
    'SystemOverview',
    'GPUStatus',
    
    # Database
    'get_database_session',
    'init_database',
    
    # Utilities
    'log_openai_usage',
    'log_usage',
    'async_log_openai_usage',
    'async_log_usage',
]
