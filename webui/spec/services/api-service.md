# API Service

## 1. Purpose
The API service provides centralized HTTP client functionality for communicating with the backend server. It handles authentication, error handling, and request/response interceptors.

## 2. Requirements
- Centralized HTTP client configuration
- Automatic JWT token attachment
- Token refresh on expiration
- Error handling and retry logic
- Base URL management
- Request/response interceptors

## 3. Design
- **Library**: Axios HTTP client
- **Base URL**: /api for backend communication
- **Timeout**: 30 seconds
- **Interceptors**: Request and response interceptors
- **Authentication**: Bearer token in Authorization header

## 4. Key Features

### Request Interceptor
- Automatically attaches JWT access token from cookies
- Handles token retrieval errors gracefully

### Response Interceptor
- Handles 401 unauthorized errors
- Automatic token refresh logic
- Prevents infinite retry loops
- Returns response data directly

### Error Handling
- Token refresh on authentication failures
- Queue requests during token refresh
- Proper error propagation

## 5. Integration
- Used by all service modules (auth, user, apikey, etc.)
- Depends on auth service for token management
- Integrated with user context for authentication state