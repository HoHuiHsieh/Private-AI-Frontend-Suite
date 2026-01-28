# -*- coding: utf-8 -*-
"""OpenAI embeddings implementation."""
import openai
import httpx
import traceback
import uuid
from logger import get_logger
from config import get_config
from .load_balancer import get_load_balancer, build_endpoint_url
from ..models import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingObject,
    EmbeddingUsage
)
from user import User
from .util import log_embeddings_usage


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


async def openai_embeddings(
    body: EmbeddingRequest,
    api_key: str = "",
    user: User = None
) -> EmbeddingResponse:
    """
    Query embeddings from OpenAI compatible API server.
    
    Args:
        body: Embedding request containing input text(s) and model
        api_key: API key for backend authentication
        user: User making the request (for usage tracking)
        
    Returns:
        EmbeddingResponse with embeddings and usage information
        
    Raises:
        ValueError: If model is not found in configuration
        RuntimeError: If API call fails
    """
    # Generate request ID for tracking
    request_id = "embd-" + str(uuid.uuid4())[:32]

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
        request_params = {
            "input": body.input,
            "model": body.model,
        }
        
        # Add optional parameters
        if body.dimensions is not None:
            request_params["dimensions"] = body.dimensions
        if body.encoding_format is not None:
            request_params["encoding_format"] = body.encoding_format
        if body.user is not None:
            request_params["user"] = body.user

        logger.debug(
            f"Sending embeddings request to OpenAI API: model={body.model}, "
            f"input_type={type(body.input).__name__}"
        )

        # Initialize OpenAI client with backend configuration
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False)
        )

        # Make API call
        response = await client.embeddings.create(**request_params)

        # Convert OpenAI response to our response model
        # OpenAI SDK returns objects, so we need to convert to dict or access attributes
        embeddings = [
            EmbeddingObject(
                object="embedding",
                embedding=item.embedding,
                index=item.index
            )
            for item in response.data
        ]
        
        usage = EmbeddingUsage(
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens
        )
        
        embedding_response = EmbeddingResponse(
            object="list",
            data=embeddings,
            model=response.model,
            usage=usage
        )

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)

        # Log usage
        # Calculate input count based on input type
        if isinstance(body.input, str):
            input_count = 1
        elif isinstance(body.input, list):
            input_count = len(body.input)
        else:
            input_count = 1

        log_embeddings_usage(
            user_id=str(user.id) if user and user.id else "unknown",
            model=body.model,
            prompt_tokens=usage.prompt_tokens,
            input_count=input_count,
            request_id=request_id,
            encoding_format=body.encoding_format,
            dimensions=body.dimensions
        )

        return embedding_response

    except openai.APIError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"OpenAI API error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Embeddings API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in embeddings: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to create embeddings: {str(e)}") from e
