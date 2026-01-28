import React, { createContext, useContext, useState, ReactNode } from 'react';
import { chatbotApi, SessionData, ChatMessage } from '@/services/chatbot';


// Define the context value shape
interface AppContextType {
    selectedItem: string | null;
    chatSession: SessionData[];
    setSelectedItem: (item: string | null) => void;
    setChatSession: (session: SessionData[]) => void;
    fetchChatSession: () => Promise<void>;
}

// Create the context
const AppContext = createContext<AppContextType | undefined>(undefined);

// 
interface AppProviderProps {
    children: ReactNode;
    entrypoint: string;
    enableChatSession?: boolean;
}

// Provider component
export const AppProvider = (props: AppProviderProps) => {
    const { children, entrypoint, enableChatSession } = props;

    // Handle side menu item selection
    const [selectedItem, setSelectedItem] = useState<string | null>(entrypoint == "new_chat" ? `chat-${Date.now()}` : entrypoint);
    const handleSetSelectedItem = (item: string | null) => {
        setSelectedItem(item);
    };

    // Handle chat session
    const [chatSession, setChatSession] = useState<SessionData[]>([]);
    // Fetch chat session
    const fetchChatSession = async () => {
        try {
            const response = await chatbotApi.listSessions();
            setChatSession(response.data);
        } catch (error) {
            console.error('Error fetching chat session:', error);
        }
    };
    React.useEffect(() => {
        // Skip fetching chat session if not enabled
        if (!enableChatSession) return;
        fetchChatSession();
    }, [setChatSession]);

    return (
        <AppContext.Provider value={{
            selectedItem,
            chatSession,
            setSelectedItem: handleSetSelectedItem,
            setChatSession: setChatSession,
            fetchChatSession: fetchChatSession
        }}>
            {children}
        </AppContext.Provider>
    );
};

// Custom hook for using the app context
export const useApp = () => {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
};