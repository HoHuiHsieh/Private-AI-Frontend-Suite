"""
Request and response models for chat completion.
Model schemas are designed to be compatible with OpenAI's "Create chat completion" API.
"""
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

# --- Chat Message Schemas ---

class ChatMessage(BaseModel):
    """Message in a chat conversation."""
    role: Literal["system", "user", "assistant", "tool", "function", "developer"]
    content: Optional[Union[str, List[dict]]] = None
    name: Optional[str] = None
    tool_calls: Optional[list] = None
    function_call: Optional[dict] = None
    refusal: Optional[str] = None
    annotations: Optional[list] = None

# --- Chat Completion Request ---

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    # Optional parameters (see OpenAI API docs)
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None # Deprecated, use max_completion_tokens
    max_completion_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    parallel_tool_calls: Optional[bool] = None
    logit_bias: Optional[dict] = None
    user: Optional[str] = None  # Deprecated, use prompt_cache_key
    tools: Optional[list] = None
    tool_choice: Optional[Union[str, dict]] = None
    response_format: Optional[dict] = None
    seed: Optional[int] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    metadata: Optional[dict] = None
    modalities: Optional[List[str]] = None
    service_tier: Optional[str] = None
    store: Optional[bool] = None
    reasoning_effort: Optional[str] = None
    # Add more fields as needed for full compatibility

# --- Chat Completion Choice ---

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None
    logprobs: Optional[dict] = None

# --- Usage Object ---

class ChatCompletionUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    prompt_tokens_details: Optional[dict] = None
    completion_tokens_details: Optional[dict] = None

# --- Chat Completion Response ---

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    service_tier: Optional[str] = None
    system_fingerprint: Optional[str] = None
    request_id: Optional[str] = None
    tool_choice: Optional[Union[str, dict]] = None
    tools: Optional[list] = None
    metadata: Optional[dict] = None
    response_format: Optional[dict] = None
    seed: Optional[int] = None

# --- Chat Completion Stream Response (Chunk) ---

class ChatCompletionStreamDelta(BaseModel):
    """Delta object in streaming response chunks."""
    role: Optional[Literal["system", "user", "assistant", "tool", "function", "developer"]] = None
    content: Optional[str] = None
    tool_calls: Optional[list] = None
    function_call: Optional[dict] = None
    refusal: Optional[str] = None

class ChatCompletionStreamChoice(BaseModel):
    """Choice object in streaming response chunks."""
    index: int
    delta: ChatCompletionStreamDelta
    finish_reason: Optional[str] = None
    logprobs: Optional[dict] = None

class ChatCompletionStreamResponse(BaseModel):
    """Streaming chunk response (object: 'chat.completion.chunk')."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]
    system_fingerprint: Optional[str] = None
    usage: Optional[ChatCompletionUsage] = None  # Only present in last chunk if stream_options={"include_usage": true}
