/**
 * Usage and Health Monitoring Service
 * This module provides endpoints for monitoring usage statistics, API health,
 * and system resources. It includes both user-specific usage data and
 * system-wide health metrics.
 */
import api from './api';

// User Usage Interfaces
export interface DailyUsage {
    date: string;
    tokens: number;
    requests: number;
}

export interface UsageOverview {
    total_tokens: number;
    total_requests: number;
    period_start: string;
    period_end: string;
    daily_data: DailyUsage[];
}

export interface ModelUsage {
    model_name: string;
    total_requests: number;
    total_tokens: number;
    period_start: string;
    period_end: string;
    daily_data: DailyUsage[];
}

export interface UsageLog {
    id: number;
    user_id: string;
    timestamp: string;
    model: string;
    api_type: string;
    prompt_tokens: number;
    completion_tokens?: number;
    total_tokens: number;
    request_id?: string;
    input_count?: number;
    extra_data?: any;
    hostname?: string;
    process_id?: number;
    created_at?: string;
}

// Health/System Interfaces
export interface SystemOverview {
    total_tokens: number;
    total_requests: number;
    total_users: number;
    active_users: number;
    period_start: string;
    period_end: string;
    daily_data: DailyUsage[];
}

export interface GPUStatus {
    gpu_id: string;
    label: string;
    memory_used_gb: number;
    memory_total_gb: number;
    utilization_percent: number;
    temperature_celsius?: number;
}

export interface UsageQueryParams {
    days?: number;
    interval?: 'day' | 'week' | 'month';
    period?: number;
    start_date?: string;
    end_date?: string;
}

// Usage Service endpoints
export const usageService = {
    // User-specific usage endpoints
    getUserOverview: (params: UsageQueryParams = { days: 30 }): Promise<UsageOverview> => {
        return api.get('/usage/overview', { params });
    },

    getUserModelUsage: (params: UsageQueryParams = { days: 30 }): Promise<ModelUsage[]> => {
        return api.get('/usage/models', { params });
    },

    getUserLogs: (skip: number = 0, limit: number = 100, params?: UsageQueryParams): Promise<UsageLog[]> => {
        return api.get('/usage/logs', {
            params: { skip, limit, ...params }
        });
    },

    // System-wide health endpoints (admin only)
    getSystemOverview: (params: UsageQueryParams = { days: 30 }): Promise<SystemOverview> => {
        return api.get('/admin/health/overview', { params });
    },

    getSystemModelUsage: (params: UsageQueryParams = { days: 30 }): Promise<ModelUsage[]> => {
        return api.get('/admin/health/models', { params });
    },

    getGPUStatus: (): Promise<GPUStatus[]> => {
        return api.get('/admin/health/gpu');
    },
};
