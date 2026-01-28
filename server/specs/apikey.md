# Module: apikey

## 1. Purpose
The apikey module handles API key management for the application.

## 2. Requirements
- API key generation and management
- API key data models
- Database setup for API key storage
- Middleware for API key authentication
- API route definitions for key operations
- Validation of API key headers

## 3. Design
- Components: manager.py (ApiKeyManager), models.py (ApiKey, ApiKeyCreate), database.py (database setup), middleware.py (get_current_user_from_api_key, validate_api_key_header), route.py (router)
- Provides middleware for authenticating via API keys
- Includes database models for API key storage
- Supports API key creation and management

## 4. Endpoints
- GET /api/apikeys - Get all API keys for the authenticated user
- POST /api/apikeys - Create a new API key for the authenticated user
- POST /api/apikeys/{key_id}/revoke - Revoke an API key