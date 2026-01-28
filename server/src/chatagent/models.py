"""
Request and response models for Chat Agent.
Model schemas are designed to be compatible with OpenAI's "Create Chat Agent" API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal, Any
from typing_extensions import TypedDict

# --- Chat Message Schemas ---


class ChatMessageArgs(TypedDict):
    id: Optional[str]
    reasoning: Optional[str]
    timestamp: Optional[int]


class ChatMessage(BaseModel):
    """Message in a chat conversation."""
    role: Literal["system", "user", "assistant",
                  "tool", "function", "developer"]
    content: Optional[Union[str, List[dict]]] = None
    name: Optional[str] = None
    tool_calls: Optional[list] = None
    function_call: Optional[dict] = None
    refusal: Optional[str] = None
    annotations: Optional[list] = None
    additional_kwargs: Optional[ChatMessageArgs] = Field(
        default_factory=dict)  # To capture any extra fields

# --- Chat Agent Request ---


class ChatAgentRequestArgs(TypedDict):
    embedding_model: Optional[str] = None
    collections: Optional[List[str]] = None


class ChatAgentRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    # Optional parameters (see OpenAI API docs)
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None  # Deprecated, use max_completion_tokens
    max_completion_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
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
    additional_kwargs: Optional[ChatAgentRequestArgs] = Field(
        default_factory=dict)  # To capture any extra fields


# --- Usage Object ---


class ChatAgentUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    prompt_tokens_details: Optional[dict] = None
    completion_tokens_details: Optional[dict] = None

# --- Chat Agent Stream Response (Chunk) ---


class ChatAgentStreamDelta(BaseModel):
    """Delta object in streaming response chunks."""
    role: Optional[Literal["system", "user", "assistant",
                           "tool", "function", "developer"]] = None
    content: Optional[str] = None
    reasoning: Optional[str] = None
    tool_calls: Optional[list] = None
    function_call: Optional[dict] = None
    refusal: Optional[str] = None


class ChatAgentStreamChoice(BaseModel):
    """Choice object in streaming response chunks."""
    index: int
    delta: ChatAgentStreamDelta
    finish_reason: Optional[str] = None
    logprobs: Optional[dict] = None


class ChatAgentStreamResponse(BaseModel):
    """Streaming chunk response (object: 'chat.completion.chunk')."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatAgentStreamChoice]
    system_fingerprint: Optional[str] = None
    # Only present in last chunk if stream_options={"include_usage": true}
    usage: Optional[ChatAgentUsage] = None

# --- Chat Agent Data Response ---


class ChatAgentData(BaseModel):
    """
    Chat Agent Session API response schema.
    """
    object: Literal["list"] = "list"
    data: List[Any]


class ChatAgentModel(TypedDict):
    """Model information."""
    chat: List[str]
    embedding: List[str]
    collections: List[str]


class ChatAgentModelListResponse(BaseModel):
    """
    Chat Agent Model List API response schema.
    """
    object: Literal["object"] = "object"
    data: ChatAgentModel


class SessionData(BaseModel):
    """
    Session data for a user conversation.
    """
    user_id: str
    session_id: str
    title: str


class ChatAgentSessionResponse(ChatAgentData):
    """
    Chat Agent Session API response schema.
    """
    data: List[SessionData]


class ChatAgentHistoryResponse(ChatAgentData):
    """
    Chat Agent History API response schema.
    """
    data: List[ChatMessage]
