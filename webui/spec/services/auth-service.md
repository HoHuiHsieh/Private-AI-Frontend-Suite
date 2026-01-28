# Authentication Service

## 1. Purpose
The authentication service manages user authentication state, JWT token handling, and session management for the webui application.

## 2. Requirements
- JWT token storage and retrieval
- Cookie-based token management
- Token refresh functionality
- Login/logout operations
- Authentication state tracking

## 3. Design
- **Token Storage**: HTTP-only cookies for security
- **Token Types**: Access and refresh tokens
- **Refresh Logic**: Automatic token refresh on expiration
- **State Management**: Integration with UserProvider context

## 4. Key Functions

### authCookies
- **getAccessToken()**: Retrieve access token from cookies
- **setAccessToken(token)**: Store access token in cookies
- **getRefreshToken()**: Retrieve refresh token from cookies
- **setRefreshToken(token)**: Store refresh token in cookies
- **clearTokens()**: Remove all tokens from cookies

### tokenRefresh
- **isRefreshing()**: Check if token refresh is in progress
- **refreshToken()**: Perform token refresh operation
- **queueRequests()**: Queue requests during refresh

### Authentication Operations
- **login(credentials)**: User login with username/password
- **logout()**: User logout and token cleanup
- **register(userData)**: User registration

## 5. Integration
- Used by API service for request authentication
- Integrated with UserProvider for state management
- Triggers UI updates on authentication changes