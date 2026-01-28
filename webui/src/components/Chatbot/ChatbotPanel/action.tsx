import React from "react";
import { ERROR_DISPLAY_DURATION } from './model';



// Types
interface StreamingState {
    isActive: boolean;
    content: string;
    reasoning: string;
    timestamp: number | null;
}

interface ChatError {
    message: string;
    timestamp: number;
}


/**
 * Custom hook for managing chat streaming state with optimized updates
 */
function useChatStreaming() {
    const [streamingState, setStreamingState] = React.useState<StreamingState>({
        isActive: false,
        content: '',
        reasoning: '',
        timestamp: null
    });
    const streamingRef = React.useRef({ content: '', reasoning: '', timestamp: null });

    const startStreaming = React.useCallback(() => {
        setStreamingState({ isActive: true, content: '', reasoning: '', timestamp: null });
        streamingRef.current = { content: '', reasoning: '', timestamp: null };
    }, []);

    const updateStreaming = React.useCallback((content: string, reasoning: string = '', timestamp: number | null = null) => {
        setStreamingState(prev => {
            const newState = {
                ...prev,
                content: prev.content + content,
                reasoning: prev.reasoning + reasoning,
                timestamp
            };
            streamingRef.current = { content: newState.content, reasoning: newState.reasoning, timestamp: newState.timestamp };
            return newState;
        });
    }, []);

    const stopStreaming = React.useCallback(() => {
        setStreamingState({ isActive: false, content: '', reasoning: '', timestamp: null });
        streamingRef.current = { content: '', reasoning: '', timestamp: null };
    }, []);

    const finalizeStreaming = React.useCallback(() => {
        const finalMessage = {
            role: 'assistant' as const,
            content: streamingRef.current.content || "",
            additional_kwargs: {
                reasoning: streamingRef.current.reasoning || undefined,
                timestamp: streamingRef.current.timestamp || undefined
            }
        };
        stopStreaming();
        return finalMessage;
    }, [stopStreaming]);

    return {
        streamingState,
        startStreaming,
        updateStreaming,
        stopStreaming,
        finalizeStreaming
    };
}

/**
 * Debounced scroll hook for performance
 */
function useDebouncedScroll(ref: React.RefObject<HTMLElement>, delay: number = 100) {
    const scrollTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

    const scrollToBottom = React.useCallback(() => {
        if (scrollTimeoutRef.current) {
            clearTimeout(scrollTimeoutRef.current);
        }

        const timeout = setTimeout(() => {
            const el = ref.current;
            if (el) {
                el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
            }
        }, delay);

        scrollTimeoutRef.current = timeout;
    }, [ref, delay]);

    React.useEffect(() => {
        return () => {
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
        };
    }, []);

    return scrollToBottom;
}

/**
 * Custom hook for managing chat errors
 */
function useChatError() {
    const [error, setError] = React.useState<ChatError | null>(null);

    const setErrorMessage = React.useCallback((message: string) => {
        setError({ message, timestamp: Date.now() });
    }, []);

    const clearError = React.useCallback(() => {
        setError(null);
    }, []);

    // Auto-clear error after duration
    React.useEffect(() => {
        if (error) {
            const timer = setTimeout(clearError, ERROR_DISPLAY_DURATION);
            return () => clearTimeout(timer);
        }
        return () => { };
    }, [error, clearError]);

    return { error, setErrorMessage, clearError };
}


export { useChatStreaming, useDebouncedScroll, useChatError };
export type { StreamingState, ChatError };