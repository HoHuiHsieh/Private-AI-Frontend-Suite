# -*- coding: utf-8 -*-
"""OpenAI responses implementation."""
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
    ResponseRequest,
    ResponseObject,
    StreamingEvent,
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


def prepare_request_params(body: ResponseRequest) -> dict:
    """
    Prepare request parameters for the OpenAI Responses API.
    """
    request_params = {}
    
    # Add all parameters if provided
    if body.model is not None:
        request_params["model"] = body.model
    if body.input is not None:
        request_params["input"] = body.input
    if body.instructions is not None:
        request_params["instructions"] = body.instructions
    if body.conversation is not None:
        request_params["conversation"] = body.conversation
    if body.previous_response_id is not None:
        request_params["previous_response_id"] = body.previous_response_id
    if body.max_output_tokens is not None:
        request_params["max_output_tokens"] = body.max_output_tokens
    if body.max_tool_calls is not None:
        request_params["max_tool_calls"] = body.max_tool_calls
    if body.metadata is not None:
        request_params["metadata"] = body.metadata
    if body.parallel_tool_calls is not None:
        request_params["parallel_tool_calls"] = body.parallel_tool_calls
    if body.prompt is not None:
        request_params["prompt"] = body.prompt
    if body.prompt_cache_key is not None:
        request_params["prompt_cache_key"] = body.prompt_cache_key
    if body.prompt_cache_retention is not None:
        request_params["prompt_cache_retention"] = body.prompt_cache_retention
    if body.reasoning is not None:
        request_params["reasoning"] = body.reasoning
    if body.safety_identifier is not None:
        request_params["safety_identifier"] = body.safety_identifier
    if body.service_tier is not None:
        request_params["service_tier"] = body.service_tier
    if body.store is not None:
        request_params["store"] = body.store
    if body.temperature is not None:
        request_params["temperature"] = body.temperature
    if body.text is not None:
        request_params["text"] = body.text
    if body.tool_choice is not None:
        request_params["tool_choice"] = body.tool_choice
    if body.tools is not None:
        request_params["tools"] = body.tools
    if body.top_logprobs is not None:
        request_params["top_logprobs"] = body.top_logprobs
    if body.top_p is not None:
        request_params["top_p"] = body.top_p
    if body.truncation is not None:
        request_params["truncation"] = body.truncation
    if body.include is not None:
        request_params["include"] = body.include
    if body.background is not None:
        request_params["background"] = body.background
    if body.user is not None:
        request_params["user"] = body.user

    return request_params


async def openai_responses(
    body: ResponseRequest,
    api_key: str = "",
    user: User = None
) -> ResponseObject:
    """
    Query responses from OpenAI compatible API server.
    """
    # Generate request ID for tracking (32 characters)
    request_id = "resp-" + str(uuid.uuid4())[:32]

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
            f"Sending request to OpenAI Responses API: {json.dumps({k: v for k, v in request_params.items() if k not in ['input', 'instructions']})}"
        )

        # Initialize OpenAI client with backend configuration
        # Use build_endpoint_url to handle both full URLs and host:port combinations
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False)
        )

        # Make API call using SDK's responses.create() method
        response = await client.responses.create(**request_params)

        # Convert SDK Response object to our ResponseObject model
        response_dict = response.model_dump()
        response_obj = ResponseObject(**response_dict)

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)

        # Log usage
        if response_obj.usage:
            usage = response_obj.usage
            log_chat_api_usage(
                user_id=str(user.id) if user and user.id else "unknown",
                model=body.model,
                prompt_tokens=usage.input_tokens or 0,
                completion_tokens=usage.output_tokens or 0,
                request_id=response_obj.id,
                reasoning_tokens=usage.output_tokens_details.reasoning_tokens if usage.output_tokens_details else 0,
                cached_tokens=usage.input_tokens_details.cached_tokens if usage.input_tokens_details else 0,
                finish_reason=response_obj.status,
                input_count=1  # Responses API has single input
            )

        return response_obj

    except openai.APIError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"OpenAI API error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Responses API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in responses: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to complete responses request: {str(e)}") from e
   

async def openai_responses_generator(
    body: ResponseRequest,
    api_key: str = "",
    user: User = None
) -> AsyncGenerator[str, None]:
    """
    Responses generator for streaming responses.
    """
    # Generate request ID for tracking (32 characters)
    request_id = "resp-" + str(uuid.uuid4())[:32]

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
            f"Sending streaming request to OpenAI Responses API: {json.dumps({k: v for k, v in request_params.items() if k not in ['input', 'instructions']})}"
        )

        # Initialize OpenAI client with backend configuration
        # Use build_endpoint_url to handle both full URLs and host:port combinations
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False)
        )

        # Track usage for final chunk
        total_input_tokens = 0
        total_output_tokens = 0
        total_reasoning_tokens = 0
        total_cached_tokens = 0
        final_status = None
        response_id = request_id

        # Ensure streaming is enabled for this request
        request_params["stream"] = True
        # Note: Responses API does not support stream_options parameter

        # Make streaming API call using SDK's responses.create() method
        stream = await client.responses.create(**request_params)

        async for event in stream:
            # Convert event to dict for serialization
            event_dict = event.model_dump(exclude_none=True)

            # Extract response ID from event (if available)
            if hasattr(event, 'response') and event.response and hasattr(event.response, 'id'):
                response_id = event.response.id

            # Extract usage information if present (typically in completed event)
            if hasattr(event, 'response') and event.response and hasattr(event.response, 'usage') and event.response.usage:
                usage = event.response.usage
                total_input_tokens = usage.input_tokens or 0
                total_output_tokens = usage.output_tokens or 0
                if usage.output_tokens_details:
                    total_reasoning_tokens = usage.output_tokens_details.reasoning_tokens or 0
                if usage.input_tokens_details:
                    total_cached_tokens = usage.input_tokens_details.cached_tokens or 0

            # Extract status if present
            if hasattr(event, 'response') and event.response and hasattr(event.response, 'status'):
                final_status = event.response.status

            # Format as SSE (Server-Sent Event)
            yield f"data: {json.dumps(event_dict)}\n\n"

        # Send final [DONE] message
        yield "data: [DONE]\n\n"

        # Log usage after stream completes
        if total_input_tokens > 0 or total_output_tokens > 0:
            log_chat_api_usage(
                user_id=str(user.id) if user and user.id else "unknown",
                model=body.model,
                prompt_tokens=total_input_tokens,
                completion_tokens=total_output_tokens,
                request_id=response_id,
                reasoning_tokens=total_reasoning_tokens,
                cached_tokens=total_cached_tokens,
                finish_reason=final_status,
                input_count=1  # Responses API has single input
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
            f"Unexpected error in streaming responses: {e}\nTraceback: {traceback.format_exc()}")
        error_data = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"
