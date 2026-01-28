# Module: usage

## 1. Purpose
The usage module handles usage tracking and health monitoring for the application.

## 2. Requirements
- User usage tracking (tokens, requests)
- System health monitoring
- Model usage statistics
- Usage logs with pagination
- Admin health endpoints
- GPU status monitoring

## 3. Design
- Components: manager.py (usage management), models.py (usage data models), database.py (usage database models), route.py (API routes), utils.py (utility functions)
- Tracks usage per user and system-wide
- Provides aggregated statistics and logs
- Includes health monitoring for system resources

## 4. Endpoints
- GET /api/usage/overview - Get usage overview for authenticated user
- GET /api/usage/models - Get model usage statistics for authenticated user
- GET /api/usage/logs - Get paginated usage logs for authenticated user
- GET /api/admin/health/overview - Get system-wide health overview (admin only)
- GET /api/admin/health/models - Get system-wide model usage (admin only)
- GET /api/admin/health/gpu - Get GPU status information (admin only)