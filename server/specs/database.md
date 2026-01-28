# Module: database

## 1. Purpose
The database module provides centralized database connection management with connection pooling, table initialization for all modules (apikey, logger, oauth2, usage), SQLAlchemy engine and session management, and database connection retrieval from the connection pool.

## 2. Requirements
- Centralized database connection management with connection pooling
- Table initialization for all modules
- SQLAlchemy engine and session management
- Database connection retrieval from connection pool
- Support for ORM operations and raw SQL operations
- Proper session lifecycle management
- Default admin user creation if configured
- Connection pool status monitoring

## 3. Design
- Uses SQLAlchemy with QueuePool for connection pooling (pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=3600)
- Provides context managers for sessions and connections
- Initializes database tables on module import
- Handles PostgreSQL timezone setting to UTC
- Includes functions for engine creation, session factory, database initialization, and cleanup
