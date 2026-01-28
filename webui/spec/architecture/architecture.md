# WebUI Architecture

## 1. Purpose
The webui is a Next.js-based frontend application that provides a user interface for interacting with the OpenAI-compatible API server. It includes three main applications: Home dashboard, OpenAI Platform interface, and RAG Chatbot.

## 2. Requirements
- Responsive web interface for API server
- User authentication and authorization
- Three main application modules (Home, OpenAI Platform, RAG Chatbot)
- Material-UI component library integration
- JWT token-based authentication
- Real-time chat capabilities with streaming
- API key management interface
- Usage statistics and monitoring

## 3. Design
- **Framework**: Next.js 15 with React 18
- **UI Library**: Material-UI (MUI) v7 with custom theming
- **State Management**: React Context (UserProvider, AppProvider)
- **API Communication**: Axios with interceptors for authentication
- **Styling**: Emotion CSS-in-JS with MUI theme system
- **Charts**: Chart.js with react-chartjs-2 and MUI X Charts
- **Data Grids**: MUI X Data Grid
- **Markdown**: react-markdown with remark-gfm and KaTeX for math
- **Build Tool**: Next.js with TypeScript

## 4. Application Structure
- **Home**: Welcome dashboard and application navigation
- **OpenAI Platform**: Interface for OpenAI-compatible API endpoints
- **RAG Chatbot**: Interactive chatbot with retrieval-augmented generation

## 5. Key Components
- **ViewPort**: Main application layout and navigation
- **Authentication**: SignIn/SignUp components with JWT handling
- **API Services**: Centralized HTTP client with token management
- **Context Providers**: Global state management for user and app data