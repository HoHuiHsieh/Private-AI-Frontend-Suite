# Module: user

## 1. Purpose
The user module handles user management, including authentication and authorization using OAuth2 protocol for webui.

## 2. Requirements
- User management functionality
- Authentication and authorization via OAuth2
- Token management (access and refresh tokens)
- Middleware for extracting user information from access tokens
- API route definitions for user operations
- Database models for users and tokens

## 3. Design
- Components: manager.py (UserManager, TokenManager), models.py (User, AccessToken, TokenData), database.py (UserDB, RefreshTokenDB), middleware.py (get_current_user, etc.), route.py (router)
- Uses OAuth2 for authentication
- Provides middleware for user extraction from tokens
- Includes database setup for user and token storage

## 4. Endpoints
- POST /api/login - Authenticate user and return access and refresh tokens
- POST /api/register - Register a new user
- POST /api/refresh - Refresh access token using refresh token
- GET /api/admin/scopes - Get list of available user scopes
- GET /api/admin/users - Get list of all users with pagination
- GET /api/admin/users/{username} - Get a specific user by username
- POST /api/admin/users - Create a new user (admin only)
- PUT /api/admin/users/{username} - Update a user (admin only)
- DELETE /api/admin/users/{username} - Delete a user (admin only)