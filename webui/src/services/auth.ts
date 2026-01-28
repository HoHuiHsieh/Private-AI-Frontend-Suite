/**
 * Authentication utilities for token management using cookies
 */

// Cookie management utilities
export const authCookies = {
    setAccessToken: (token: string, expiresIn: number) => {
        // expiresIn is in seconds, convert to days
        const days = expiresIn / (60 * 60 * 24);
        document.cookie = `access_token=${token}; path=/; max-age=${expiresIn}; SameSite=Strict; Secure`;
    },

    setRefreshToken: (token: string) => {
        // Refresh token typically has longer expiry (e.g., 30 days)
        const maxAge = 30 * 24 * 60 * 60; // 30 days in seconds
        document.cookie = `refresh_token=${token}; path=/; max-age=${maxAge}; SameSite=Strict; Secure`;
    },

    getAccessToken: (): string | null => {
        const match = document.cookie.match(/(^|;)\s*access_token\s*=\s*([^;]+)/);
        return match ? (match[2] ?? null) : null;
    },

    getRefreshToken: (): string | null => {
        const match = document.cookie.match(/(^|;)\s*refresh_token\s*=\s*([^;]+)/);
        return match ? (match[2] ?? null) : null;
    },

    removeTokens: () => {
        document.cookie = 'access_token=; path=/; max-age=0; SameSite=Strict; Secure';
        document.cookie = 'refresh_token=; path=/; max-age=0; SameSite=Strict; Secure';
    },

    hasValidToken: (): boolean => {
        return !!authCookies.getAccessToken();
    }
};

// Token refresh logic
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

export const tokenRefresh = {
    subscribeTokenRefresh: (callback: (token: string) => void) => {
        refreshSubscribers.push(callback);
    },

    onTokenRefreshed: (token: string) => {
        refreshSubscribers.forEach(callback => callback(token));
        refreshSubscribers = [];
    },

    isRefreshing: () => isRefreshing,
    
    setRefreshing: (value: boolean) => {
        isRefreshing = value;
    }
};

// Logout utility
export const logout = () => {
    authCookies.removeTokens();
    // Clear any other auth-related data
    // Optionally redirect to login page
    // window.location.href = '/webui';
};
