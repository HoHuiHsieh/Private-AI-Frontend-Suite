# OpenAI-Compatible API WebUI

A Next.js-based web interface for the OpenAI-compatible API server, providing user-friendly access to AI models, chat functionality, and administrative features.

## Features

- **Three Main Applications**: Home dashboard, OpenAI Platform interface, and RAG Chatbot
- **User Authentication**: JWT-based login and registration system
- **API Key Management**: Secure API key generation and administration
- **Real-time Chat**: Streaming chat interface with AI models
- **Usage Monitoring**: Comprehensive usage statistics and system health
- **Admin Panel**: User management and system administration
- **Responsive Design**: Mobile and desktop-friendly interface
- **Material-UI**: Modern, accessible component library

## Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Running backend API server

### Installation

1. Install dependencies:
   
   Make sure to run this command before production builds as well.
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:8080`

### Build for Production

Build the application for static file serving:

```bash
npm run build
```

The static files will be generated in the `out/` directory and can be served by any static file server (nginx, Apache, etc.).

### Build Output

- **Build Directory**: `out/` - Contains optimized production static files
- **Static Assets**: Served from `out/_next/static/`
- **Pages**: Pre-rendered HTML files optimized for production
- **Static Export**: Ready for deployment to any static hosting service

### Deployment Options

- **Static Hosting**: Deploy `out/` directory to any web server
- **CDN**: Serve static files through a CDN for better performance
- **Vercel/Netlify**: Deploy directly with their static hosting integration
- **Docker**: Containerize with nginx to serve the static files from `out/`


## Main Applications

### Home
- Welcome dashboard and application navigation
- Overview of available features

### OpenAI Platform
- API key management and administration
- Usage statistics and monitoring
- User management (admin)
- System health monitoring
- Settings and configuration

### RAG Chatbot
- Interactive chat with AI models
- Session management and history
- Real-time streaming responses
- Model selection and configuration

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── favicon.ico
├── components/            # Reusable UI components
│   ├── OpenAiPlatform/    # OpenAI Platform components
│   ├── HomePage/          # Home page components
│   ├── Chatbot/           # Chatbot components
│   ├── SignIn.tsx         # Authentication forms
│   ├── SignUp.tsx
│   ├── MenuButton.tsx     # Navigation components
│   └── ViewPort/          # Main layout
├── context/               # React context providers
│   ├── UserProvider.tsx   # User authentication state
│   └── AppProvider.tsx    # Application state
├── services/              # API service layer
│   ├── api.ts            # HTTP client
│   ├── auth.ts           # Authentication
│   ├── user.ts           # User operations
│   ├── apikey.ts         # API key management
│   ├── usage.ts          # Usage statistics
│   └── chatbot.ts        # Chat functionality
└── theme/                # Material-UI theming
```

## Configuration

The webui uses Next.js environment variables for configuration. Environment variables are set at build time and can be configured through your deployment platform or build scripts.

## Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production (static files)
- `npm run lint` - Run ESLint

### Module Specifications
Detailed specifications for each component and service are available in the `spec/` directory:

- [Architecture](spec/architecture/architecture.md)
- [Applications](spec/applications/)
  - [Home](spec/applications/home.md)
  - [OpenAI Platform](spec/applications/openai-platform.md)
  - [Chatbot](spec/applications/chatbot.md)
- [Services](spec/services/)
- [Components](spec/components/)
- [Context Providers](spec/context/)
- [System Configuration](spec/system/)

## Technology Stack

- **Framework**: Next.js 15 with React 18 (static export)
- **UI Library**: Material-UI (MUI) v7
- **Styling**: Emotion CSS-in-JS
- **Charts**: Chart.js with MUI X Charts
- **Data Grids**: MUI X Data Grid
- **Language**: TypeScript
- **Build Tool**: Next.js with SWC compiler
- **Deployment**: Static file hosting

## License

See LICENSE.txt in the root directory.