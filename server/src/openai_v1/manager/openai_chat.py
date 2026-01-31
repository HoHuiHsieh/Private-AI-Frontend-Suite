# -*- coding: utf-8 -*-
"""OpenAI chat completion implementation."""
import openai
import httpx
import traceback
import uuid
import json
from typing import AsyncGenerator, Union
from logger import get_logger
from config import get_config, ModelConfig
from .load_balancer import get_load_balancer, build_endpoint_url
from ..models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatCompletionStreamResponse,
    ChatMessage
)
from user import User
from .util import log_chat_api_usage


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


def prepare_request_params(body: ChatCompletionRequest) -> dict:
    """
    Prepare request parameters for the OpenAI API.
    """
    request_params = {
        "model": body.model,
        "messages": [msg.model_dump(exclude_none=True) for msg in body.messages],
    }

    # Add optional parameters if provided
    if body.frequency_penalty is not None:
        request_params["frequency_penalty"] = body.frequency_penalty
    if body.logit_bias is not None:
        request_params["logit_bias"] = body.logit_bias
    if body.logprobs is not None:
        request_params["logprobs"] = body.logprobs
    if body.top_logprobs is not None:
        request_params["top_logprobs"] = body.top_logprobs
    if body.max_tokens is not None:
        raise NotImplementedError(
            "Max tokens are deprecated, use max_completion_tokens.")
    if body.max_completion_tokens is not None:
        request_params["max_completion_tokens"] = body.max_completion_tokens
    if body.n is not None:
        request_params["n"] = body.n
    if body.presence_penalty is not None:
        request_params["presence_penalty"] = body.presence_penalty
    if body.response_format is not None:
        request_params["response_format"] = body.response_format
    if body.seed is not None:
        request_params["seed"] = body.seed
    if body.stop is not None:
        request_params["stop"] = body.stop
    if body.temperature is not None:
        request_params["temperature"] = body.temperature
    if body.top_p is not None:
        request_params["top_p"] = body.top_p
    if body.tools is not None:
        request_params["tools"] = body.tools
    if body.tool_choice is not None:
        request_params["tool_choice"] = body.tool_choice
    # Note: parallel_tool_calls is not supported by TensorRT-LLM backend
    if body.parallel_tool_calls is not None and body.parallel_tool_calls:
        # request_params["parallel_tool_calls"] = body.parallel_tool_calls
        raise NotImplementedError("Parallel tool calls are not supported.")

    return request_params


async def openai_chat_completion(
    body: ChatCompletionRequest,
    api_key: str = "",
    user: User = None
) -> ChatCompletionResponse:
    """
    Query chat completion from OpenAI compatible API server.
    """
    # Generate request ID for tracking (32 characters)
    request_id = "chatcmpl-" + str(uuid.uuid4())[:32]

    # Get model configuration
    model = config.get_model_config(body.model)
    if not model:
        logger.error(f"Model not found: {body.model}")
        raise ValueError(f"Model not found: {body.model}")

    # Select endpoint using load balancer
    lb = get_load_balancer()
    host, port = lb.get_endpoint(model.host, model.port, body.model)

    # Mark request start for connection tracking
    lb.mark_request_start(host, port, body.model)

    try:
        # Prepare request parameters
        request_params = prepare_request_params(body)

        # Ensure streaming is disabled for non-streaming response
        request_params["stream"] = False

        logger.debug(
            f"Sending request to OpenAI API: {json.dumps({k: v for k, v in request_params.items() if k != 'messages'})}")

        # Initialize OpenAI client with backend configuration
        # Use build_endpoint_url to handle both full URLs and host:port combinations
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False),
        )

        # Make API call
        response = await client.chat.completions.create(
            **request_params,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )

        # Convert OpenAI response to our response model
        # OpenAI SDK returns objects, so we need to convert to dict or access attributes
        choices = [
            ChatCompletionChoice(
                index=choice.index,
                message=ChatMessage(
                    role=choice.message.role,
                    content=choice.message.content,
                    # fixed tool_calls and function_call extraction
                    tool_calls=[tc.model_dump() for tc in choice.message.tool_calls] if hasattr(
                        choice.message, 'tool_calls') and choice.message.tool_calls else None,
                    function_call=choice.message.function_call.model_dump() if hasattr(
                        choice.message, 'function_call') and choice.message.function_call else None
                ),
                finish_reason=choice.finish_reason,
                logprobs=choice.logprobs if hasattr(
                    choice, 'logprobs') else None
            )
            for choice in response.choices
        ]

        usage = ChatCompletionUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )

        chat_response = ChatCompletionResponse(
            id=response.id,
            object=response.object,
            created=response.created,
            model=response.model,
            choices=choices,
            usage=usage,
            system_fingerprint=response.system_fingerprint if hasattr(
                response, 'system_fingerprint') else None
        )

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)

        # Log usage
        if usage:
            log_chat_api_usage(
                user_id=str(user.id) if user.id else "unknown",
                model=body.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                request_id=response.id,
                reasoning_tokens=usage.completion_tokens_details.get('reasoning_tokens', 0) if hasattr(
                    usage, 'completion_tokens_details') and usage.completion_tokens_details else 0,
                cached_tokens=usage.prompt_tokens_details.get('cached_tokens', 0) if hasattr(
                    usage, 'prompt_tokens_details') and usage.prompt_tokens_details else 0,
                finish_reason=choices[0].finish_reason if choices else None,
                input_count=len(body.messages)
            )

        return chat_response

    except openai.APIError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"OpenAI API error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Chat completion API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in chat completion: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to complete chat request: {str(e)}") from e


async def openai_chat_completion_generator(
    body: ChatCompletionRequest,
    api_key: str = "",
    user: User = None
) -> AsyncGenerator[str, None]:
    """
    Chat completion generator for streaming responses.
    """
    # Generate request ID for tracking (32 characters)
    request_id = "chatcmpl-" + str(uuid.uuid4())[:32]

    # Get model configuration
    model = config.get_model_config(body.model)
    if not model:
        logger.error(f"Model not found: {body.model}")
        raise ValueError(f"Model not found: {body.model}")

    # Select endpoint using load balancer
    lb = get_load_balancer()
    host, port = lb.get_endpoint(model.host, model.port, body.model)

    # Mark request start for connection tracking
    lb.mark_request_start(host, port, body.model)

    try:
        # Prepare request parameters
        request_params = prepare_request_params(body)

        logger.debug(
            f"Sending request to OpenAI API: {json.dumps({k: v for k, v in request_params.items() if k != 'messages'})}")

        # Initialize OpenAI client with backend configuration
        # Use build_endpoint_url to handle both full URLs and host:port combinations
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False)
        )

        # Track usage for final chunk
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_reasoning_tokens = 0
        total_cached_tokens = 0
        finish_reason = None

        # Ensure streaming is enabled for this request
        request_params["stream"] = True
        request_params["stream_options"] = {
            "include_usage": True}  # To get usage in final chunk

        # Disable thinking indicator in chat template
        request_params["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}}

        # Make streaming API call
        stream = await client.chat.completions.create(**request_params)

        async for chunk in stream:
            # Convert chunk to dict for serialization
            chunk_dict = chunk.model_dump(exclude_none=True)

            # Extract usage information if present (final chunk)
            if chunk.usage:
                total_prompt_tokens = chunk.usage.prompt_tokens
                total_completion_tokens = chunk.usage.completion_tokens
                if hasattr(chunk.usage, 'completion_tokens_details') and chunk.usage.completion_tokens_details:
                    total_reasoning_tokens = getattr(
                        chunk.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if hasattr(chunk.usage, 'prompt_tokens_details') and chunk.usage.prompt_tokens_details:
                    total_cached_tokens = getattr(
                        chunk.usage.prompt_tokens_details, 'cached_tokens', 0)

            # Extract finish reason if present
            if chunk.choices and chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

            # Format as SSE (Server-Sent Event)
            yield f"data: {json.dumps(chunk_dict)}\n\n"

        # Send final [DONE] message
        yield "data: [DONE]\n\n"

        # Log usage after stream completes
        if total_prompt_tokens > 0 or total_completion_tokens > 0:
            log_chat_api_usage(
                user_id=str(user.id) if user.id else "unknown",
                model=body.model,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                request_id=request_id,
                reasoning_tokens=total_reasoning_tokens,
                cached_tokens=total_cached_tokens,
                finish_reason=finish_reason,
                input_count=len(body.messages)
            )

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)

    except openai.APIError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"OpenAI API error during streaming: {e}\nTraceback: {traceback.format_exc()}")
        error_data = {
            "error": {
                "message": str(e),
                "type": "api_error",
                "code": getattr(e, 'code', None)
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in streaming chat completion: {e}\nTraceback: {traceback.format_exc()}")
        error_data = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"
