# UserProvider Context

## 1. Purpose
The UserProvider context manages global user authentication state and user data throughout the webui application.

## 2. Requirements
- Global user state management
- Authentication status tracking
- User data persistence
- Permission level management
- Login/logout state handling

## 3. Design
- **Context**: React Context API implementation
- **Provider**: UserProvider component wrapping the app
- **State**: User data, authentication status, permissions
- **Actions**: Login, logout, user data updates

## 4. State Structure

### User Data
- **id**: User unique identifier
- **username**: User's login name
- **email**: User's email address
- **fullname**: User's display name
- **active**: Account active status
- **scopes**: User permission scopes

### Authentication State
- **isAuthenticated**: Boolean authentication status
- **isLoading**: Loading state for auth operations
- **permission**: Numeric permission level (0=guest, 10=user, 20=admin)

## 5. Key Functions

### Authentication
- **login(credentials)**: Perform user login
- **logout()**: Perform user logout
- **register(userData)**: User registration
- **refreshAuth()**: Refresh authentication state

### State Management
- **setUser(user)**: Update user data
- **clearUser()**: Clear user state
- **updatePermission(level)**: Update permission level

## 6. Integration
- Wraps the entire application
- Used by all components requiring user data
- Integrates with authentication service
- Provides user state to API service