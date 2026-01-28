# Chatbot Service

## 1. Purpose
The chatbot service handles chat session management, message operations, and real-time communication with the AI chat backend.

## 2. Requirements
- Chat session creation and management
- Message sending and receiving
- Streaming response handling
- Chat history retrieval
- Message CRUD operations

## 3. Design
- **API Endpoints**: /api/chatagent/* endpoints
- **Streaming**: Server-sent events for real-time responses
- **Session Management**: Persistent chat sessions
- **Message Handling**: Full message lifecycle management

## 4. Key Functions

### Session Management
- **getChatSessions()**: List user's chat sessions
- **createChatSession()**: Start new chat session
- **deleteChatSession(sessionId)**: Remove chat session

### Message Operations
- **getChatHistory(sessionId)**: Retrieve conversation history
- **sendMessage(sessionId, message)**: Send message and get response
- **getMessage(messageId)**: Get specific message details
- **updateMessage(messageId, content)**: Edit message content
- **deleteMessage(messageId)**: Remove message from session

### Streaming
- **streamChatResponse()**: Handle streaming AI responses
- **processStreamData()**: Parse and display streaming content

## 5. Integration
- Used by Chatbot component interface
- Integrated with authentication for user sessions
- Provides real-time chat functionality