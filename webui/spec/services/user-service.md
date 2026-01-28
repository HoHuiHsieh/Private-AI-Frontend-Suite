# User Service

## 1. Purpose
The user service handles user-related API operations including profile management, user administration, and user data retrieval.

## 2. Requirements
- User profile operations
- Admin user management
- User data retrieval and updates
- User listing and search
- Role and permission management

## 3. Design
- **API Endpoints**: /api/admin/users and related endpoints
- **Authentication**: Requires appropriate user permissions
- **Data Models**: User objects with roles and permissions
- **Operations**: CRUD operations for user management

## 4. Key Functions

### User Profile
- **getCurrentUser()**: Get current authenticated user data
- **updateProfile(userData)**: Update user profile information

### Admin Operations
- **getUsers(params)**: List all users with pagination
- **getUserById(id)**: Get specific user details
- **createUser(userData)**: Create new user (admin only)
- **updateUser(id, userData)**: Update user information (admin only)
- **deleteUser(id)**: Delete user (admin only)

### User Scopes
- **getScopes()**: Retrieve available user permission scopes
- **updateUserScopes(id, scopes)**: Update user permissions

## 5. Integration
- Used by admin interface for user management
- Integrated with authentication service
- Provides data for user context provider