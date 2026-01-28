/**
 * Chat Agent API Service
 * This module provides endpoints for interacting with the chat agent functionality in the application.
 * It includes functionality for sending messages, retrieving conversation history,
 * and managing chat conversations.
 */
import api from './api';
import { authCookies } from './auth';

// Type definitions matching the server-side models

export type MessageRole = "system" | "user" | "assistant" | "tool" | "function" | "developer";

export interface ChatMessageArgs {
    id?: string | null;
    reasoning?: string | null;
    timestamp?: number | null;
}

export interface ChatMessage {
    role: MessageRole;
    content?: string | Array<any> | null;
    name?: string | null;
    tool_calls?: Array<any> | null;
    function_call?: Record<string, any> | null;
    refusal?: string | null;
    annotations?: Array<any> | null;
    additional_kwargs?: ChatMessageArgs | null;
}

export interface ChatAgentRequestArgs {
    embedding_model?: string | null;
    collections?: string[] | null;
}

export interface ChatAgentRequest {
    model: string;
    messages: ChatMessage[];
    temperature?: number;
    top_p?: number;
    n?: number;
    stream?: boolean;
    stop?: string | string[] | null;
    max_tokens?: number | null;
    max_completion_tokens?: number | null;
    presence_penalty?: number;
    frequency_penalty?: number;
    parallel_tool_calls?: boolean | null;
    logit_bias?: Record<string, number> | null;
    user?: string | null;
    tools?: Array<any> | null;
    tool_choice?: string | Record<string, any> | null;
    response_format?: Record<string, any> | null;
    seed?: number | null;
    logprobs?: boolean | null;
    top_logprobs?: number | null;
    metadata?: Record<string, any> | null;
    modalities?: string[] | null;
    service_tier?: string | null;
    store?: boolean | null;
    reasoning_effort?: string | null;
    additional_kwargs?: ChatAgentRequestArgs | null;
}

export interface ChatAgentUsage {
    prompt_tokens?: number | null;
    completion_tokens?: number | null;
    total_tokens?: number | null;
    prompt_tokens_details?: Record<string, any> | null;
    completion_tokens_details?: Record<string, any> | null;
}

export interface ChatAgentStreamDelta {
    role?: MessageRole | null;
    content?: string | null;
    reasoning?: string | null;
    tool_calls?: Array<any> | null;
    function_call?: Record<string, any> | null;
    refusal?: string | null;
}

export interface ChatAgentStreamChoice {
    index: number;
    delta: ChatAgentStreamDelta;
    finish_reason?: string | null;
    logprobs?: Record<string, any> | null;
}

export interface ChatAgentStreamResponse {
    id: string;
    object: "chat.completion.chunk";
    created: number;
    model: string;
    choices: ChatAgentStreamChoice[];
    system_fingerprint?: string | null;
    usage?: ChatAgentUsage | null;
    timestamp?: number | null;
}

export interface SessionData {
    user_id: string;
    session_id: string;
    title: string;
}

export interface ChatAgentSessionResponse {
    object: "list";
    data: SessionData[];
}

export interface ChatAgentHistoryResponse {
    object: "list";
    data: ChatMessage[];
}

export interface ChatAgentModel {
    chat: string[];
    embedding: string[];
    collections: string[];
}

export interface ChatAgentModelListResponse {
    object: "object";
    data: ChatAgentModel;
}

/**
 * Utility function to parse Server-Sent Events (SSE) stream
 * @param stream - The ReadableStream from the fetch response
 * @param onChunk - Callback function to handle each parsed chunk
 * @param onError - Optional callback function to handle errors
 * @param onComplete - Optional callback function called when stream completes
 */
export async function parseSSEStream(
    stream: ReadableStream,
    onChunk: (data: ChatAgentStreamResponse) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
): Promise<void> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (onComplete) onComplete();
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');

            // Keep the last incomplete line in the buffer
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6); // Remove 'data: ' prefix
                        if (jsonStr.trim()) {
                            const data = JSON.parse(jsonStr) as ChatAgentStreamResponse;
                            onChunk(data);
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE chunk:', e);
                        if (onError) onError(e as Error);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error reading stream:', error);
        if (onError) onError(error as Error);
    } finally {
        reader.releaseLock();
    }
}

// Chatbot API endpoints
export const chatbotApi = {
    /**
     * Send a message to the chat agent and receive a streaming response
     * This endpoint streams responses using Server-Sent Events (SSE)
     * @param sessionId - The unique session identifier
     * @param request - The chat request containing model, messages, and parameters
     * @returns A ReadableStream of server-sent events
     */
    chat: async (sessionId: string, request: ChatAgentRequest): Promise<ReadableStream> => {
        const accessToken = authCookies.getAccessToken();

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000000); // 5 minutes timeout

        try {
            const response = await fetch(`/api/chatagent/chat/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken || ''}`,
                },
                body: JSON.stringify(request),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            if (!response.body) {
                throw new Error('Response body is null');
            }

            return response.body;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timed out after 5 minutes');
            }
            throw error;
        }
    },

    /**
     * Get the list of chat sessions for the current user
     * @returns The chat session response containing all sessions with metadata
     */
    listSessions: (): Promise<ChatAgentSessionResponse> => {
        return api.get('/chatagent/sessions');
    },

    /**
     * Get the chat history for a specific session
     * @param sessionId - The unique session identifier
     * @returns The chat history response containing all messages
     */
    getHistory: (sessionId: string): Promise<ChatAgentHistoryResponse> => {
        return api.get(`/chatagent/chat/${sessionId}`);
    },

    /**
     * Delete the chat history for a specific session
     * @param sessionId - The unique session identifier
     * @returns A promise that resolves when the history is deleted
     */
    deleteHistory: (sessionId: string): Promise<void> => {
        return api.delete(`/chatagent/chat/${sessionId}`);
    },

    /**
     * Get a specific message from a session
     * @param sessionId - The unique session identifier
     * @param messageId - The unique message identifier
     * @returns A promise that resolves to the message
     */
    getMessage: (sessionId: string, messageId: string): Promise<ChatMessage> => {
        return api.get(`/chatagent/message/${messageId}/chat/${sessionId}`);
    },

    /**
     * Update a specific message in a session
     * @param sessionId - The unique session identifier
     * @param messageId - The unique message identifier
     * @param message - The updated message data
     * @returns A promise that resolves when the message is updated
     */
    updateMessage: (sessionId: string, messageId: string, message: ChatMessage): Promise<void> => {
        return api.post(`/chatagent/message/${messageId}/chat/${sessionId}`, message);
    },

    /**
     * Delete a specific message from a session
     * @param sessionId - The unique session identifier
     * @param messageId - The unique message identifier
     * @returns A promise that resolves when the message is deleted
     */
    deleteMessage: (sessionId: string, messageId: string): Promise<void> => {
        return api.delete(`/chatagent/message/${messageId}/chat/${sessionId}`);
    },

    /**
     * Get the list of available models for the chat agent
     * @returns A promise that resolves to the model list response
     */
    getModelList: (): Promise<ChatAgentModelListResponse> => {
        return api.get('/chatagent/models');
    }
};
