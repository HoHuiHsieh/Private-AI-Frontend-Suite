# OpenAI-Compatible API Server

A FastAPI-based server providing OpenAI-compatible API endpoints with user management, API key authentication, and various AI model integrations.

## Features

- **OpenAI API v1 Compatibility**: Chat completions, embeddings, audio transcription, and model management
- **User Management**: OAuth2 authentication with JWT tokens
- **API Key Management**: Secure API key generation and validation
- **Chat Agent**: Interactive chat sessions with streaming support
- **Usage Tracking**: Comprehensive usage monitoring and health statistics
- **Database Integration**: PostgreSQL with connection pooling
- **Logging**: Configurable logging with database and console backends

## Start Development Server:

```bash
bash ./serve.sh
```

## API Endpoints

### OpenAI v1 API
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/embeddings` - Text embeddings
- `POST /v1/audio/transcriptions` - Audio transcription
- `POST /v1/responses` - Model responses

### Authentication
- `POST /api/login` - User login
- `POST /api/register` - User registration
- `POST /api/refresh` - Token refresh

### API Keys
- `GET /api/apikeys` - List API keys
- `POST /api/apikeys` - Create API key
- `POST /api/apikeys/{id}/revoke` - Revoke API key

### Chat Agent
- `GET /api/chatagent/models` - Chat agent models
- `GET /api/chatagent/sessions` - User sessions
- `POST /api/chatagent/chat/{session_id}` - Chat interaction

### Usage & Admin
- `GET /api/usage/overview` - User usage stats
- `GET /api/admin/health/overview` - System health
- `GET /api/admin/users` - User management

## Project Structure

```
src/
├── main.py                 # FastAPI application entry point
├── database/               # Database connection and models
├── config/                 # Configuration management
├── logger/                 # Logging system
├── user/                   # User authentication and management
├── apikey/                 # API key management
├── openai_v1/              # OpenAI API v1 implementation
├── chatagent/              # Chat agent functionality
├── usage/                  # Usage tracking and monitoring
└── specs/                  # Module specifications
```

## Configuration

The server uses environment variables for configuration. Key settings include:

- Database connection string
- JWT secret keys
- Model configurations
- Logging levels
- Admin user credentials

See the config module documentation for complete configuration options.

## Development

### Running Tests
```bash
pytest test/
```

### Module Specifications
Detailed specifications for each module are available in the `specs/` directory:

- [Database Module](specs/database.md)
- [Config Module](specs/config.md)
- [Logger Module](specs/logger.md)
- [User Module](specs/user.md)
- [API Key Module](specs/apikey.md)
- [OpenAI v1 Module](specs/openai_v1.md)
- [Chat Agent Module](specs/chatagent.md)
- [Usage Module](specs/usage.md)

## License

See LICENSE.txt in the root directory.