/**
 * User Management API Service
 * This module provides endpoints for managing users in the application.
 * It includes functionality for listing users, retrieving user details,
 * creating new users, updating existing users, deleting users, and managing scopes.
 * It is intended for use by administrators to manage user accounts and permissions.
 */
import api, { setUserApiInstance } from './api';

export interface AccessToken {
    access_token: string;
    token_type: string;
    expires_in: number;
    refresh_token?: string;
    fullname?: string;
    email?: string;
    username?: string;
    role?: 'guest' | 'user' | 'admin';
}

export interface LoginCredentials {
    username: string;
    password: string;
    scope?: string;
}

export interface RegisterData {
    username: string;
    email: string;
    fullname: string;
    password: string;
}

export interface User {
    id: number;
    username: string;
    email: string;
    fullname: string;
    active: boolean;
    scopes: string[];
    created_at: string;
    updated_at?: string;
}

export interface UserCreate {
    username: string;
    password: string;
    email: string;
    fullname: string;
    active?: boolean;
    scopes?: string[];
}

export interface UserUpdate {
    email?: string;
    fullname?: string;
    password?: string;
    active?: boolean;
    scopes?: string[];
}

export interface UserResponse {
    id: number;
    username: string;
    email: string;
    fullname: string;
    active: boolean;
    scopes: string[];
    created_at: string;
    updated_at?: string;
}

// User Management API endpoints
export const userApi = {
    // Authentication
    login: (credentials: LoginCredentials): Promise<AccessToken> => {
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);
        formData.append('scope', credentials.scope || '');
        return api.post('/login', formData);
    },

    register: (data: RegisterData): Promise<User> => {
        return api.post('/register', data);
    },

    refreshToken: (refresh_token: string): Promise<AccessToken> => {
        return api.post('/refresh', { refresh_token });
    },

    // Scopes Management
    getAvailableScopes: (): Promise<string[]> => {
        return api.get('/admin/scopes');
    },

    // Admin User Management
    listUsers: (skip: number = 0, limit: number = 100): Promise<UserResponse[]> => {
        return api.get('/admin/users', {
            params: { skip, limit }
        });
    },

    getUser: (username: string): Promise<UserResponse> => {
        return api.get(`/admin/users/${username}`);
    },

    createUser: (userData: UserCreate): Promise<UserResponse> => {
        return api.post('/admin/users', userData);
    },

    updateUser: (username: string, userUpdate: UserUpdate): Promise<UserResponse> => {
        return api.put(`/admin/users/${username}`, userUpdate);
    },

    deleteUser: (username: string): Promise<{ detail: string }> => {
        return api.delete(`/admin/users/${username}`);
    },
};

// Set the userApi instance in api.ts to avoid circular dependency
setUserApiInstance(userApi);

