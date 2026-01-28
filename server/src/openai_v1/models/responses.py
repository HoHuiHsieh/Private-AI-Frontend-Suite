"""
Request and response models for OpenAI Responses API.

Core Models:
    - ResponseRequest: Request model for creating responses (POST /v1/responses)
    - ResponseObject: Non-streaming response object
    - StreamingEvent: Streaming response events (when stream=True)

API Reference: https://platform.openai.com/docs/api-reference/responses

Last Updated: 2026-01-08
OpenAI API Version: 2025-04-14
"""

from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel


# --- Request Model ---
class ResponseRequest(BaseModel):
    """Request model for creating a response (POST /v1/responses)."""
    model: Optional[str] = None
    input: Optional[Union[str, List[Any]]] = None
    instructions: Optional[Union[str, List[str]]] = None
    conversation: Optional[Union[str, Dict[str, Any]]] = None
    previous_response_id: Optional[str] = None
    max_output_tokens: Optional[int] = None
    max_tool_calls: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None
    parallel_tool_calls: Optional[bool] = True
    prompt: Optional[Dict[str, Any]] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_retention: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    safety_identifier: Optional[str] = None
    service_tier: Optional[str] = None
    store: Optional[bool] = True
    stream: Optional[bool] = False
    stream_options: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 1.0
    text: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = 1.0
    truncation: Optional[str] = "disabled"
    include: Optional[List[str]] = None
    background: Optional[bool] = False
    user: Optional[str] = None  # Deprecated


# --- Non-Streaming Response Model ---
class ResponseOutputContent(BaseModel):
    """Content within an output item."""
    type: str
    text: Optional[str] = None
    annotations: Optional[List[Any]] = None


class ResponseOutputItem(BaseModel):
    """An output item in the response."""
    type: str
    id: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    content: Optional[List[ResponseOutputContent]] = None
    encrypted_content: Optional[str] = None


class ResponseUsageDetails(BaseModel):
    """Token usage details."""
    cached_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None


class ResponseUsage(BaseModel):
    """Token usage information."""
    input_tokens: Optional[int] = None
    input_tokens_details: Optional[ResponseUsageDetails] = None
    output_tokens: Optional[int] = None
    output_tokens_details: Optional[ResponseUsageDetails] = None
    total_tokens: Optional[int] = None


class ResponseObject(BaseModel):
    """Non-streaming response object (when stream=False)."""
    id: str
    object: Literal["response"] = "response"
    created_at: int
    status: str
    completed_at: Optional[int] = None
    error: Optional[Dict[str, Any]] = None
    incomplete_details: Optional[Dict[str, Any]] = None
    instructions: Optional[Union[str, List[str]]] = None
    max_output_tokens: Optional[int] = None
    model: Optional[str] = None
    output: Optional[List[ResponseOutputItem]] = None
    parallel_tool_calls: Optional[bool] = None
    previous_response_id: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    store: Optional[bool] = None
    temperature: Optional[float] = None
    text: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    top_p: Optional[float] = None
    truncation: Optional[str] = None
    usage: Optional[ResponseUsage] = None
    user: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    service_tier: Optional[str] = None
    conversation: Optional[Dict[str, Any]] = None
    prompt: Optional[Dict[str, Any]] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_retention: Optional[str] = None
    background: Optional[bool] = None


# --- Streaming Response Models ---
class StreamingEventBase(BaseModel):
    """Base class for streaming events."""
    type: str
    sequence_number: int


class ResponseCreatedEvent(StreamingEventBase):
    type: Literal["response.created"] = "response.created"
    response: ResponseObject


class ResponseInProgressEvent(StreamingEventBase):
    type: Literal["response.in_progress"] = "response.in_progress"
    response: ResponseObject


class ResponseCompletedEvent(StreamingEventBase):
    type: Literal["response.completed"] = "response.completed"
    response: ResponseObject


class ResponseFailedEvent(StreamingEventBase):
    type: Literal["response.failed"] = "response.failed"
    response: ResponseObject


class ResponseIncompleteEvent(StreamingEventBase):
    type: Literal["response.incomplete"] = "response.incomplete"
    response: ResponseObject


class ResponseQueuedEvent(StreamingEventBase):
    type: Literal["response.queued"] = "response.queued"
    response: ResponseObject


class ResponseOutputItemAddedEvent(StreamingEventBase):
    type: Literal["response.output_item.added"] = "response.output_item.added"
    output_index: int
    item: ResponseOutputItem


class ResponseOutputItemDoneEvent(StreamingEventBase):
    type: Literal["response.output_item.done"] = "response.output_item.done"
    output_index: int
    item: ResponseOutputItem


class ResponseContentPartAddedEvent(StreamingEventBase):
    type: Literal["response.content_part.added"] = "response.content_part.added"
    item_id: str
    output_index: int
    content_index: int
    part: ResponseOutputContent


class ResponseContentPartDoneEvent(StreamingEventBase):
    type: Literal["response.content_part.done"] = "response.content_part.done"
    item_id: str
    output_index: int
    content_index: int
    part: ResponseOutputContent


class ResponseOutputTextDeltaEvent(StreamingEventBase):
    type: Literal["response.output_text.delta"] = "response.output_text.delta"
    item_id: str
    output_index: int
    content_index: int
    delta: str
    logprobs: Optional[List[Any]] = None


class ResponseOutputTextDoneEvent(StreamingEventBase):
    type: Literal["response.output_text.done"] = "response.output_text.done"
    item_id: str
    output_index: int
    content_index: int
    text: str
    logprobs: Optional[List[Any]] = None


class ResponseRefusalDeltaEvent(StreamingEventBase):
    type: Literal["response.refusal.delta"] = "response.refusal.delta"
    item_id: str
    output_index: int
    content_index: int
    delta: str


class ResponseRefusalDoneEvent(StreamingEventBase):
    type: Literal["response.refusal.done"] = "response.refusal.done"
    item_id: str
    output_index: int
    content_index: int
    refusal: str


class ResponseFunctionCallArgumentsDeltaEvent(StreamingEventBase):
    type: Literal["response.function_call_arguments.delta"] = "response.function_call_arguments.delta"
    item_id: str
    output_index: int
    delta: str


class ResponseFunctionCallArgumentsDoneEvent(StreamingEventBase):
    type: Literal["response.function_call_arguments.done"] = "response.function_call_arguments.done"
    item_id: str
    output_index: int
    name: str
    arguments: str


class ResponseFileSearchCallInProgressEvent(StreamingEventBase):
    type: Literal["response.file_search_call.in_progress"] = "response.file_search_call.in_progress"
    output_index: int
    item_id: str


class ResponseFileSearchCallSearchingEvent(StreamingEventBase):
    type: Literal["response.file_search_call.searching"] = "response.file_search_call.searching"
    output_index: int
    item_id: str


class ResponseFileSearchCallCompletedEvent(StreamingEventBase):
    type: Literal["response.file_search_call.completed"] = "response.file_search_call.completed"
    output_index: int
    item_id: str


class ResponseWebSearchCallInProgressEvent(StreamingEventBase):
    type: Literal["response.web_search_call.in_progress"] = "response.web_search_call.in_progress"
    output_index: int
    item_id: str


class ResponseWebSearchCallSearchingEvent(StreamingEventBase):
    type: Literal["response.web_search_call.searching"] = "response.web_search_call.searching"
    output_index: int
    item_id: str


class ResponseWebSearchCallCompletedEvent(StreamingEventBase):
    type: Literal["response.web_search_call.completed"] = "response.web_search_call.completed"
    output_index: int
    item_id: str


class ResponseReasoningTextDeltaEvent(StreamingEventBase):
    type: Literal["response.reasoning_text.delta"] = "response.reasoning_text.delta"
    item_id: str
    output_index: int
    content_index: int
    delta: str


class ResponseReasoningTextDoneEvent(StreamingEventBase):
    type: Literal["response.reasoning_text.done"] = "response.reasoning_text.done"
    item_id: str
    output_index: int
    content_index: int
    text: str


class ResponseCodeInterpreterCallInProgressEvent(StreamingEventBase):
    type: Literal["response.code_interpreter_call.in_progress"] = "response.code_interpreter_call.in_progress"
    output_index: int
    item_id: str


class ResponseCodeInterpreterCallInterpretingEvent(StreamingEventBase):
    type: Literal["response.code_interpreter_call.interpreting"] = "response.code_interpreter_call.interpreting"
    output_index: int
    item_id: str


class ResponseCodeInterpreterCallCompletedEvent(StreamingEventBase):
    type: Literal["response.code_interpreter_call.completed"] = "response.code_interpreter_call.completed"
    output_index: int
    item_id: str


class ResponseCodeInterpreterCallCodeDeltaEvent(StreamingEventBase):
    type: Literal["response.code_interpreter_call_code.delta"] = "response.code_interpreter_call_code.delta"
    output_index: int
    item_id: str
    delta: str


class ResponseCodeInterpreterCallCodeDoneEvent(StreamingEventBase):
    type: Literal["response.code_interpreter_call_code.done"] = "response.code_interpreter_call_code.done"
    output_index: int
    item_id: str
    code: str


class StreamingErrorEvent(StreamingEventBase):
    type: Literal["error"] = "error"
    code: str
    message: str
    param: Optional[str] = None


# Union type for all streaming events (when stream=True)
StreamingEvent = Union[
    ResponseCreatedEvent,
    ResponseInProgressEvent,
    ResponseCompletedEvent,
    ResponseFailedEvent,
    ResponseIncompleteEvent,
    ResponseQueuedEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseOutputTextDeltaEvent,
    ResponseOutputTextDoneEvent,
    ResponseRefusalDeltaEvent,
    ResponseRefusalDoneEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseFileSearchCallInProgressEvent,
    ResponseFileSearchCallSearchingEvent,
    ResponseFileSearchCallCompletedEvent,
    ResponseWebSearchCallInProgressEvent,
    ResponseWebSearchCallSearchingEvent,
    ResponseWebSearchCallCompletedEvent,
    ResponseReasoningTextDeltaEvent,
    ResponseReasoningTextDoneEvent,
    ResponseCodeInterpreterCallInProgressEvent,
    ResponseCodeInterpreterCallInterpretingEvent,
    ResponseCodeInterpreterCallCompletedEvent,
    ResponseCodeInterpreterCallCodeDeltaEvent,
    ResponseCodeInterpreterCallCodeDoneEvent,
    StreamingErrorEvent,
]
