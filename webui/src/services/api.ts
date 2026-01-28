/**
 * API service for making HTTP requests
 * This module sets up an axios instance with a base URL and includes an interceptor
 * to automatically attach the authentication token from cookies to each request.
 * It is used throughout the application to interact with the backend API.
 */

import axios from 'axios';
import { authCookies, tokenRefresh, logout } from './auth';

// Avoid circular dependency by importing userApi after it's defined
let userApiInstance: any = null;

export const setUserApiInstance = (instance: any) => {
    userApiInstance = instance;
};

// Create axios instance with base configuration
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

// Add a request interceptor to include the authentication token
api.interceptors.request.use(
    (config) => {
        try {
            const accessToken = authCookies.getAccessToken();
            if (accessToken) {
                config.headers['Authorization'] = `Bearer ${accessToken}`;
            }
        } catch (e) {
            console.error('Failed to get access token', e);
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle errors and token refresh
api.interceptors.response.use(
    (response) => response.data,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (tokenRefresh.isRefreshing()) {
                // If already refreshing, wait for the new token
                return new Promise((resolve) => {
                    tokenRefresh.subscribeTokenRefresh((token: string) => {
                        originalRequest.headers['Authorization'] = `Bearer ${token}`;
                        resolve(axios(originalRequest));
                    });
                });
            }

            originalRequest._retry = true;
            tokenRefresh.setRefreshing(true);

            try {
                const refreshToken = authCookies.getRefreshToken();
                
                if (!refreshToken) {
                    // No refresh token available, logout
                    logout();
                    return Promise.reject(error);
                }

                // Call refresh token endpoint
                const response = await userApiInstance.refreshToken(refreshToken);

                const { access_token, expires_in, refresh_token: newRefreshToken } = response;

                // Store new tokens
                authCookies.setAccessToken(access_token, expires_in);
                if (newRefreshToken) {
                    authCookies.setRefreshToken(newRefreshToken);
                }

                // Update authorization header
                originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

                // Notify subscribers
                tokenRefresh.onTokenRefreshed(access_token);
                tokenRefresh.setRefreshing(false);

                // Retry original request
                return axios(originalRequest);
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                tokenRefresh.setRefreshing(false);
                logout();
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
