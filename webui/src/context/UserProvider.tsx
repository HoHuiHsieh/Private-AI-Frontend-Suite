import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authCookies } from '@/services/auth';
import { userApi } from '@/services/user';

// Define the shape of the user object
export interface User {
  role: 'guest' | 'user' | 'admin';
  name?: string;
  email?: string;
  imgsrc?: string;
}

// Define the context value shape
interface UserContextType {
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
  isInitializing: boolean;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
}

// Create the context
const UserContext = createContext<UserContextType | undefined>(undefined);

// Provider component
export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  // Handle font size selection
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const handleSetFontSize = (size: 'small' | 'medium' | 'large') => {
    setFontSize(size);
  }

  // Check for existing refresh token on mount and restore session
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const refreshToken = authCookies.getRefreshToken();

        if (refreshToken) {
          // Refresh the access token
          const tokenResponse = await userApi.refreshToken(refreshToken);

          // Store new tokens
          authCookies.setAccessToken(tokenResponse.access_token, tokenResponse.expires_in);
          if (tokenResponse.refresh_token) {
            authCookies.setRefreshToken(tokenResponse.refresh_token);
          }

          // Restore user session
          const userName = tokenResponse.fullname || tokenResponse.username;
          const userEmail = tokenResponse.email;
          setUser({
            role: (tokenResponse as any).role || 'user',
            ...(userName && { name: userName }),
            ...(userEmail && { email: userEmail }),
            imgsrc: '',
          });

        }
      } catch (error) {
        console.error('Failed to restore session:', error);
        // Clear invalid tokens
        authCookies.removeTokens();
      } finally {
        setIsInitializing(false);
      }
    };

    initializeAuth();
  }, []);

  const login = (userData: User) => {
    setUser(userData);
  };

  const logout = () => {
    // Clear auth cookies
    authCookies.removeTokens();
    // Clear user state
    setUser(null);
  };

  return (
    <UserContext.Provider value={{
      user,
      login,
      logout,
      isInitializing,
      fontSize,
      setFontSize: handleSetFontSize
    }}>
      {children}
    </UserContext.Provider>
  );
};

// Custom hook for using the user context
export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
