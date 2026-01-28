# General Information

Welcome to the AI Service Platform Dashboard, hosted on local servers. This dashboard allows you to manage your api keys, monitor usage, and configure settings.

## Overview

This dashboard provides a comprehensive interface for managing your AI Service Platform resources.

## Features

- **API Key Management**: Create, view, and manage your API keys securely
- **Usage Tracking**: Monitor your API usage and costs
- **Settings**: Customize your experience with theme and font size options

## Getting Started

1. Create a new API key from the **API Keys** section
2. Store your secret key securely
3. Use the key in your applications to access AI Service Platform services

## Best Practices

- Never share your API keys publicly
- Rotate keys regularly for enhanced security
- Monitor your usage to stay within budget
- Use descriptive names for your API keys

## OpenAI API Compatibility

The AI Service Platform is compatible with the following OpenAI APIs. You can use existing OpenAI client libraries to interact with the platform by pointing them to your self-hosted server.

> **Note:** The Chat and Responses APIs currently support **text-only** interactions. Image or other media types are not supported at this time.

### Models

```bash
curl http://<your_server_address>/v1/models \
  --header "Authorization: Bearer YOUR_API_KEY"
```

or using Python:

```python
import openai
openai.api_base = "http://<your_server_address>/v1"
openai.api_key = "YOUR_API_KEY"
models = openai.Model.list()
print(models)
```

### Chat Completions

```bash
curl http://<your_server_address>/v1/chat/completions \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "qwen3-30b-a3b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

or using Python:

```python
import openai
openai.api_base = "http://<your_server_address>/v1"
openai.api_key = "YOUR_API_KEY"
response = openai.ChatCompletion.create(
    model="qwen3-30b-a3b",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response)
```

### Responses API

```bash
curl http://<your_server_address>/v1/responses \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "qwen3-30b-a3b",
    "input": "Hello!"
  }'
```

or using Python:

```python
import openai
openai.api_base = "http://<your_server_address>/v1"
openai.api_key = "YOUR_API_KEY"
response = openai.Responses.create(
    model="qwen3-30b-a3b",
    input="Hello!"
)
print(response)
```


### Embeddings

```bash
curl http://<your_server_address>/v1/embeddings \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "embeddinggemma-300m",
    "input": "Hello world"
  }'
```

or using Python:

```python
import openai
openai.api_base = "http://<your_server_address>/v1"
openai.api_key = "YOUR_API_KEY"
response = openai.Embedding.create(
    model="embeddinggemma-300m",
    input="Hello world"
)
print(response)
```

### Available Models

The platform currently supports the following models:

- **qwen3-30b-a3b**: Chat completion and responses model
- **embeddinggemma-300m**: Text embedding model

### Authentication

All API requests require authentication using an API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

You can create and manage API keys through the dashboard's API Keys section.



## Support

Please refer to administrator or support channels for assistance with this platform.