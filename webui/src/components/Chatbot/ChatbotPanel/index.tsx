import React from 'react';
import { MessageList, MessageType } from 'react-chat-elements';
import { micromark } from 'micromark';
import parse from 'html-react-parser';
import { gfmTable, gfmTableHtml } from 'micromark-extension-gfm-table';
import { math, mathHtml } from 'micromark-extension-math';
import { Stack, Box, IconButton, TextField, Typography, Alert, InputAdornment, Tooltip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import SettingsIcon from '@mui/icons-material/Settings';
import { useApp } from '@/context/AppProvider';
import PlaylistRemoveIcon from '@mui/icons-material/PlaylistRemove';
import { chatbotApi, ChatMessage, parseSSEStream, ChatAgentRequest } from '@/services/chatbot';
import ConfigDrawer, { ChatConfig } from './ConfigDrawer';
import { useChatStreaming, useDebouncedScroll, useChatError } from './action';
import ReasoningDialog from './ReasoningDialog';
import { DEFAULT_SYSTEM_PROMPT } from './model';
import './index.css';
import 'react-chat-elements/dist/main.css';
import 'katex/dist/katex.min.css';


// Helper function to read file as base64
const readFileAsBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

// Helper function to convert markdown to HTML
const convertMarkdownToHtml = (markdownText: string, reasoning: string = "") => {
    // Clean LaTeX syntax errors
    let cleaned = markdownText
    // .replace(/;=;/g, '=')  // Replace ;=; with =
    // .replace(/;\\(\w+);/g, '\\$1')  // Replace ;\pm; with \pm, etc.
    // .replace(/,(\w)/g, '$1')  // Remove , before letters
    // .replace(/(\w),/g, '$1'); // Remove , after letters
    // Wrap LaTeX expressions in $ if not already
    // cleaned = cleaned.replace(/\[([^\]]*)\]/g, (match, content) => {
    //     if (content.includes('\\')) {
    //         return '$' + content + '$';
    //     }
    //     return match;
    // });
    let html = micromark(cleaned || '',
        {
            extensions: [gfmTable(), math()],
            htmlExtensions: [gfmTableHtml(), mathHtml()],
        }
    );
    html = html.replace(/^<p>/, '').replace(/<\/p>$/, '');
    html = `<div class='markdown-container'>${html}</div>`;
    return html;
};

// Helper function to map ChatMessage to MessageType
const mapChatMessagesToMessageType = (chatMessages: ChatMessage[]): MessageType[] => {
    return chatMessages.map((msg, index) => {
        let text = '';
        if (typeof msg.content === 'string') {
            text = parse(convertMarkdownToHtml(msg.content)) as string;
        } else if (Array.isArray(msg.content)) {
            const textPart = msg.content.find(c => c.type === 'text');
            text = textPart ? parse(convertMarkdownToHtml(textPart.text)) as string : '';
        }
        if (msg.role === 'system') {
            return {
                type: 'system',
                title: 'System Message',
                text: text,
                id: msg.additional_kwargs?.id || `msg-${Date.now()}`,
            } as MessageType;
        } else if (msg.role === 'user' || msg.role === 'assistant') {
            return {
                type: 'text',
                title: msg.role === 'user' ? 'User' : 'AI',
                text: text,
                date: new Date(msg.additional_kwargs?.timestamp || Date.now()),
                position: msg.role === 'user' ? 'right' : 'left',
                id: msg.additional_kwargs?.id || `msg-${Date.now()}`,
                reply: msg.additional_kwargs?.reasoning ? {
                    title: 'Reference',
                    message: msg.additional_kwargs.reasoning,
                } : undefined,
                removeButton: msg.role === 'user' ? true : false,
            } as MessageType;
        }
        return {
            type: 'text',
            title: 'Error',
            text: 'Unsupported message type',
            date: new Date(),
            position: 'left',
            id: msg.additional_kwargs?.id || `msg-${Date.now()}`,
        } as MessageType;
    });
};


// Interfaces
interface ChatbotPanelProps {
    // Add props if needed
}

/**
 * ChatbotPanel component - Main chat interface using react-chat-elements with MUI
 * @param props - Component props
 * @returns ChatbotPanel component
 */
export default function ChatbotPanel(props: ChatbotPanelProps) {
    const { selectedItem, fetchChatSession } = useApp();

    // State management
    const [inputValue, setInputValue] = React.useState('');
    const [drawerOpen, setDrawerOpen] = React.useState(false);
    const [chatConfig, setChatConfig] = React.useState<ChatConfig>({
        model: '',
        embedding: '',
        system_prompt: DEFAULT_SYSTEM_PROMPT,
        temperature: 1.0,
        top_p: 1.0,
        collections: [],
    });
    const [chatHistory, setChatHistory] = React.useState<Map<string, ChatMessage[]>>(new Map());
    const [messages, setMessages] = React.useState<MessageType[]>([]);
    const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
    const [openReasoning, setOpenReasoning] = React.useState<string>('');
    const listRef = React.useRef<HTMLDivElement | null>(null);
    const fileInputRef = React.useRef<HTMLInputElement | null>(null);

    // Custom hooks
    const { streamingState, startStreaming, updateStreaming, stopStreaming, finalizeStreaming } = useChatStreaming();
    const { error, setErrorMessage, clearError } = useChatError();
    const scrollToBottom = useDebouncedScroll(listRef);

    // Fetch chat history when selected item changes
    const fetchChatHistory = React.useCallback(async () => {
        if (!selectedItem.startsWith('chat-')) return;
        let historyMessages: ChatMessage[] = [];
        try {
            const chatSession = selectedItem.replace('chat-', '');
            const response = await chatbotApi.getHistory(chatSession);
            // historyMessages = response.data.filter(msg => msg.role !== 'system');
            historyMessages = response.data;
        } catch (error) {
            setErrorMessage('Initializing chat session.');
        } finally {
            setChatHistory(prev => new Map(prev).set(selectedItem, historyMessages));
            const mappedMessages = mapChatMessagesToMessageType(historyMessages);
            setMessages(mappedMessages);
        }
    }, [selectedItem, setErrorMessage, setChatHistory, setMessages]);
    React.useEffect(() => {
        fetchChatHistory();
    }, [selectedItem, setErrorMessage, fetchChatHistory]);

    // Append message to chat history and messages
    const appendMessage = (msg: ChatMessage) => {
        setChatHistory(prev => {
            const history = new Map(prev);
            const messages = history.get(selectedItem) || [];
            history.set(selectedItem, [...messages, msg]);
            return history;
        });
        const newMessageType = mapChatMessagesToMessageType([msg])[0];
        setMessages(prev => [...prev, newMessageType]);
    };

    // Auto-scroll to bottom when content changes
    React.useEffect(() => {
        scrollToBottom();
    }, [messages.length, streamingState.content, scrollToBottom]);

    // Update system prompt on update
    const fetchEditSystemMessage = React.useCallback(async (system_prompt: string) => {
        const history = chatHistory.get(selectedItem);
        if (history && history.length > 0 && history[0].role === 'system') {
            try {
                const updatedSystemMessage = {
                    ...history[0],
                    content: system_prompt,
                }
                await chatbotApi.updateMessage(
                    selectedItem.replace('chat-', ''),
                    updatedSystemMessage.additional_kwargs?.id || '',
                    updatedSystemMessage
                );
            } catch (error) {
                console.error('Error updating system prompt:', error);
                setErrorMessage('Failed to update system prompt');
            } finally {
                // Sleep 500ms before fetching updated history
                await new Promise(resolve => setTimeout(resolve, 500));
                await fetchChatHistory();
            }
        }
    }, [chatHistory, selectedItem, setErrorMessage, fetchChatHistory]);

    React.useEffect(() => {
        if (drawerOpen === false) {
            fetchEditSystemMessage(chatConfig.system_prompt);
        }
    }, [chatConfig.system_prompt, drawerOpen]);

    // Update streaming message
    const streamingMessage = React.useMemo(() => {
        if (streamingState.isActive && !streamingState.content) {
            return {
                type: 'text',
                title: 'AI',
                text: parse('<div>Processing...<br><div class="progress-bar"><div class="progress-fill"></div></div></div>'),
                date: new Date(),
                position: 'left',
                id: 'streaming',
                reply: streamingState.reasoning ? {
                    title: 'Reference',
                    message: streamingState.reasoning,
                } : undefined,
            } as MessageType;
        } else if (streamingState.isActive && streamingState.content) {
            const text = parse(convertMarkdownToHtml(streamingState.content)) as string;
            return {
                type: 'text',
                title: 'AI',
                text: text,
                date: new Date(),
                position: 'left',
                id: 'streaming',
                reply: streamingState.reasoning ? {
                    title: 'Reference',
                    message: streamingState.reasoning,
                } : undefined,
            } as MessageType;
        }
        return null;
    }, [streamingState.content, streamingState.reasoning, streamingState.isActive]);

    // Send message to AI
    const sendToAI = React.useCallback(async (text: string, file?: File) => {
        if (!selectedItem.startsWith('chat-')) return;
        const sessionId = selectedItem.replace('chat-', '');
        let content: any = text;
        if (file) {
            const base64 = await readFileAsBase64(file);
            content = [
                { type: "text", text: text ? text : 'Summarize this file in under 50 words.' },
                { type: "file", file: { file_data: base64, file_name: file.name } }
            ];
        }
        const userMessage: ChatMessage = {
            role: 'user',
            content: content,
        };
        appendMessage(userMessage);

        const history = chatHistory.get(selectedItem) || [];
        let messagesForRequest = [] as ChatMessage[];
        if (history.length === 0) {
            messagesForRequest = [
                { role: 'system', content: chatConfig.system_prompt },
                userMessage
            ];
        } else {
            messagesForRequest = [userMessage];
        }

        const request: ChatAgentRequest = {
            model: chatConfig.model,
            messages: messagesForRequest,
            temperature: chatConfig.temperature,
            top_p: chatConfig.top_p,
            stream: true,
            additional_kwargs: {
                embedding_model: chatConfig.embedding,
                collections: chatConfig.collections,
            },
        };
        try {
            startStreaming();
            const stream = await chatbotApi.chat(sessionId, request);
            await parseSSEStream(
                stream,
                (data) => {
                    const delta = data.choices[0]?.delta;
                    if (delta) {
                        updateStreaming(delta.content || '', delta.reasoning || '', data.created);
                    }
                },
                (error) => {
                    console.error('Streaming error:', error);
                    setErrorMessage('Error during streaming');
                    stopStreaming();
                },
                () => {
                    const finalMessage = finalizeStreaming();
                    appendMessage(finalMessage);
                }
            );
        } catch (error) {
            console.error('Error sending message:', error);
            setErrorMessage('Failed to send message');
            stopStreaming();
        } finally {
            // Sleep 500ms before fetching updated history
            await new Promise(resolve => setTimeout(resolve, 500));
            await fetchChatSession();
            await fetchChatHistory();
        }
    }, [selectedFile, selectedItem, chatConfig, chatHistory, appendMessage, startStreaming, updateStreaming, stopStreaming, finalizeStreaming, setErrorMessage, fetchChatSession, fetchChatHistory]);

    // Handle remove message
    const handleRemoveMessage = async (msg: MessageType) => {
        try {
            const sessionId = selectedItem.replace('chat-', '');
            await chatbotApi.deleteMessage(sessionId, `${msg.id}`);
        } catch (error) {
            console.error('Error removing message:', error);
            setErrorMessage('Failed to remove message');
            return;
        } finally {
            // Sleep 500ms before fetching updated history
            await new Promise(resolve => setTimeout(resolve, 500));
            await fetchChatSession();
            await fetchChatHistory();
        }
    }


    // Handle send
    const handleSend = () => {
        if (inputValue.trim() || selectedFile) {
            sendToAI(inputValue.trim(), selectedFile || undefined);
            setInputValue('');
            setSelectedFile(null);
        }
    };

    // Handle file upload
    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
        }
        setErrorMessage(`Selected file: ${file?.name}`);
    };

    // Handle key press
    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>Chatbot</Typography>
                <IconButton onClick={() => setDrawerOpen(true)}>
                    <SettingsIcon />
                </IconButton>
            </Box>

            {/* Message List */}
            <Box
                sx={{
                    flexGrow: 1,
                    overflow: 'auto',
                    color: 'grey.800',
                }}
                ref={listRef}
            >
                <MessageList
                    className="message-list"
                    lockable={true}
                    toBottomHeight={'100%'}
                    dataSource={streamingMessage ? [...messages, streamingMessage] : messages}
                    referance={listRef}
                    onReplyMessageClick={(item) => setOpenReasoning(item.reply?.message || '')}
                    onRemoveMessageClick={handleRemoveMessage}
                />
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ m: 1 }} onClose={clearError}>
                    {error.message}
                </Alert>
            )}

            {/* Input Area */}
            <Stack direction="row" alignItems="center" spacing={1} sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                <TextField
                    fullWidth
                    placeholder="Type a message..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    disabled={streamingState.isActive}
                    sx={{ mr: 1, '& .MuiInputBase-root': { height: 'auto' } }}
                    multiline
                    minRows={1}
                    maxRows={5}
                    slotProps={{
                        input: {
                            endAdornment: selectedFile ? (
                                <InputAdornment position="end">
                                    <Tooltip title={`Remove file: ${selectedFile.name}`}>
                                        <IconButton size='medium' onClick={() => setSelectedFile(null)}>
                                            <PlaylistRemoveIcon fontSize='small' sx={{ color: 'warning.main' }} />
                                        </IconButton>
                                    </Tooltip>
                                </InputAdornment>
                            ) : undefined,
                        }
                    }}
                />
                <Tooltip title={`Upload File`}>
                    <IconButton onClick={() => fileInputRef.current?.click()} disabled={streamingState.isActive}>
                        <AttachFileIcon fontSize='small' />
                    </IconButton>
                </Tooltip>
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept=".txt,.md,.pdf,.docx"
                    onChange={handleFileUpload}
                />
                <Tooltip title={`Voice Input (Coming Soon)`}>
                    <span>
                        <IconButton disabled>
                            <MicIcon fontSize='small' />
                        </IconButton>
                    </span>
                </Tooltip>
                <Tooltip title={`Send Message`}>
                    <span>
                        <IconButton onClick={handleSend} disabled={(!inputValue.trim() && !selectedFile) || streamingState.isActive}>
                            <SendIcon fontSize='small' sx={{ color: 'primary.main' }} />
                        </IconButton>
                    </span>
                </Tooltip>
            </Stack>

            {/* Config Drawer */}
            <ConfigDrawer
                open={drawerOpen}
                value={chatConfig}
                onOpen={() => setDrawerOpen(true)}
                onClose={() => setDrawerOpen(false)}
                onChange={setChatConfig}
            />

            {/* Reasoning Dialog */}
            <ReasoningDialog
                open={openReasoning !== ''}
                onClose={() => setOpenReasoning('')}
                content={openReasoning}
            />
        </Box>
    );
}