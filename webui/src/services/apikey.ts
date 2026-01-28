/**
 * API Key Management Service
 * This module provides endpoints for managing API keys in the application.
 * It includes functionality for listing, creating, and revoking API keys.
 */
import api from './api';

export interface ApiKey {
    id: number;
    api_key: string;
    user_id: number;
    expires_at: string;
    revoked: boolean;
    created_at: string;
    name?: string;
}

export interface ApiKeyCreate {
    name: string;
    days?: number;
}

export interface ApiKeyResponse {
    id: number;
    api_key: string;
    user_id: number;
    expires_at: string;
    revoked: boolean;
    created_at: string;
    name?: string;
}

// API Key Management endpoints
export const apiKeyService = {
    // List all API keys for the current user
    listKeys: (): Promise<ApiKeyResponse[]> => {
        return api.get('/apikeys');
    },

    // Create a new API key
    createKey: (keyData: ApiKeyCreate): Promise<ApiKeyResponse> => {
        return api.post('/apikeys', keyData);
    },

    // Revoke an API key
    revokeKey: (keyId: number): Promise<{ detail: string }> => {
        return api.post(`/apikeys/${keyId}/revoke`);
    },
};
