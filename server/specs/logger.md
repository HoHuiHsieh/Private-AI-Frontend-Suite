# Module: logger

## 1. Purpose
The logger module provides a configurable logging system with console and database backend support. It includes asynchronous logging capabilities, log rotation, structured logging, and automatic fallback mechanisms.

## 2. Requirements
- PostgreSQL database logging with automatic table creation
- Automatic database log rotation based on retention policy
- Asynchronous logging using queue handlers
- Configurable log levels (global and per-component)
- Graceful fallback to console logging on database errors
- Comprehensive log record fields including hostname and stack traces
- Structured logging with context data

## 3. Design
- Main component: LoggerManager class for managing loggers
- Global logger manager instance
- Functions: initialize_logger(), get_logger(name), shutdown_logging()
- Supports console and database backends
- Asynchronous queue handlers for performance