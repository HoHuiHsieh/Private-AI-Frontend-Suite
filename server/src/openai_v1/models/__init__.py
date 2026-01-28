"""
OpenAI-compatible Pydantic models for all major API endpoints.

This package provides request, response, and streaming event schemas for:
	- /v1/models (model listing)
	- /v1/chat/completions (chat completions)
	- /v1/embeddings (embeddings)
	- /v1/audio/transcriptions (audio transcription)
	- /v1/responses (advanced responses, streaming, tool calls, etc.)

Each submodule is strictly aligned with the latest OpenAI API documentation.

Usage:
	from openai_v1.models import *

Modules:
	- models: Model listing schemas
	- chat: Chat completion schemas
	- embeddings: Embedding request/response schemas
	- audio_transcription: Audio transcription schemas
	- responses: Advanced response and streaming event schemas

Last updated: 2026-01-06
"""
from .models import *
from .chat import *
from .embeddings import *
from .audio_transcription import *
from .responses import *
