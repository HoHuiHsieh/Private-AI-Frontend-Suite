# -*- coding: utf-8 -*-
"""Triton embeddings implementation using gRPC client."""
import tritonclient.grpc as grpcclient
from tritonclient.utils import InferenceServerException
import base64
import traceback
import uuid
import numpy as np
from typing import List
from logger import get_logger
from config import get_config, ModelConfig
from .load_balancer import get_load_balancer, build_endpoint_url, is_full_url
from ..models import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingObject,
    EmbeddingUsage
)
from user import User
from .util import log_embeddings_usage, estimate_tokens


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


async def triton_embeddings(
    body: EmbeddingRequest,
    api_key: str = "",
    user: User = None
) -> EmbeddingResponse:
    """
    Query embeddings from Triton inference server using gRPC.

    Supports:
    - Single string or list of strings input
    - Custom dimensions for text-embedding-3 models
    - Float or base64 encoding formats
    - User tracking for monitoring

    Args:
        body: Embedding request containing input text(s) and model
        api_key: API key for authentication (not used for Triton)
        user: User making the request (for usage tracking)

    Returns:
        EmbeddingResponse with embeddings and usage information

    Raises:
        ValueError: If model is not found or input is invalid
        RuntimeError: If Triton server query fails
    """
    # Generate request ID for tracking
    request_id = "embd-" + str(uuid.uuid4())[:32]

    # Get model configuration
    model = config.get_model_config(body.model)
    if not model:
        logger.error(f"Model not found: {body.model}")
        raise ValueError(f"Model not found: {body.model}")

    # Prepare input data - convert to list if single string
    if isinstance(body.input, str):
        text_input = [body.input]
    elif isinstance(body.input, list):
        # Handle list of strings or list of token IDs
        if all(isinstance(item, str) for item in body.input):
            text_input = body.input
        else:
            # For token IDs, we would need to decode them first
            # For now, convert to strings
            text_input = [str(item) for item in body.input]
    else:
        text_input = [str(body.input)]

    # Validate input constraints
    if len(text_input) > 2048:
        raise ValueError("Input array must be 2048 dimensions or less")

    logger.info(
        f"Triton embeddings request - Model: {body.model}, Inputs: {len(text_input)}, "
        f"Format: {body.encoding_format}, Dimensions: {body.dimensions}"
    )

    # Prepare inputs to the format expected by Triton
    inputs: List[grpcclient.InferInput] = []

    # Determine input format based on number of texts
    if len(text_input) == 1:
        # Single query mode - use "query" input with shape [1]
        query_input = grpcclient.InferInput("query", [1], "BYTES")
        query_data = np.array([text_input[0]], dtype=object)
        query_input.set_data_from_numpy(query_data)
        inputs.append(query_input)
        logger.debug(
            f"Using query mode - single input: {text_input[0][:100]}...")
    else:
        # Multiple documents mode - use "documents" input with shape [1, num_docs]
        documents_input = grpcclient.InferInput(
            "documents", [1, len(text_input)], "BYTES")
        documents_data = np.array([text_input], dtype=object)
        documents_input.set_data_from_numpy(documents_data)
        inputs.append(documents_input)
        logger.debug(f"Using documents mode - {len(text_input)} inputs")

    logger.debug(
        f"Embeddings input count: {len(text_input)}, total chars: {sum(len(str(t)) for t in text_input)}")

    # Prepare outputs to the format expected by Triton
    outputs = [grpcclient.InferRequestedOutput("embeddings")]

    # Select endpoint using load balancer
    lb = get_load_balancer()
    host, port = lb.get_endpoint(model.host, model.port, body.model)

    # Mark request start for connection tracking
    lb.mark_request_start(host, port, body.model)

    # Build endpoint URL (handle both full URLs and host:port)
    if is_full_url(host):
        # Extract host:port from URL for gRPC client
        # For gRPC, we need to strip the protocol
        grpc_url = host.replace('https://', '').replace('http://', '')
    else:
        grpc_url = f"{host}:{port}"

    try:
        # Prepare Triton client
        triton_client = grpcclient.InferenceServerClient(
            url=grpc_url,
            verbose=False,
        )

        logger.debug(
            f"Using gRPC Triton server at {grpc_url} for model {body.model} (load balanced)")

        # Send inference request
        response = triton_client.infer(
            model_name=body.model,
            inputs=inputs,
            outputs=outputs,
            request_id=request_id,
            timeout=3000000  # 5 minutes timeout
        )

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)
        logger.debug(
            f"Received response from Triton server at {host}:{port} for model {body.model}")

        # Extract the embedding data from the response
        embedding_data = response.as_numpy("embeddings")
        if embedding_data is None:
            logger.error(
                f"Failed to get embedding data from Triton server at {host}:{port} for model {body.model}")
            raise ValueError(
                f"Failed to get embedding data from Triton server for model {body.model}")

        # Verify embedding data format
        if not isinstance(embedding_data, np.ndarray):
            logger.error(
                f"Invalid embedding data format received from Triton server: {type(embedding_data)}")
            raise ValueError(
                f"Invalid embedding data format received from Triton server for model {body.model}")

        if embedding_data.dtype != np.float32:
            logger.warning(
                f"Unexpected embedding data type: {embedding_data.dtype}, expected np.float32. Attempting to convert.")
            try:
                embedding_data = embedding_data.astype(np.float32)
            except Exception as e:
                logger.error(f"Error converting embedding data type: {str(e)}")
                raise ValueError(
                    f"Failed to convert embedding data type for model {body.model}") from e

        logger.debug(
            f"Embedding data shape: {embedding_data.shape}, type: {embedding_data.dtype}")

        # Handle different response shapes
        # For single query: shape is (1, embedding_dim) or (embedding_dim,)
        # For multiple documents: shape is (num_docs, embedding_dim)
        if embedding_data.ndim == 1:
            # Single embedding returned as 1D array
            embedding_data = [embedding_data]
        elif embedding_data.ndim == 2 and len(text_input) == 1:
            # Single query returned as 2D array with shape (1, dim)
            embedding_data = embedding_data
        # else: multiple documents, shape is already (num_docs, dim)

        # Validate dimensions if requested
        if body.dimensions is not None:
            actual_dims = embedding_data.shape[1] if len(
                embedding_data.shape) > 1 else len(embedding_data[0])
            if actual_dims != body.dimensions:
                logger.warning(
                    f"Requested dimensions ({body.dimensions}) differ from actual ({actual_dims}). "
                    f"This may indicate the model doesn't support custom dimensions."
                )

        # Verify embeddings are normalized (L2 norm should be ~1.0)
        for i, embed in enumerate(embedding_data):
            norm = np.linalg.norm(embed)
            logger.debug(f"Embedding {i} norm: {norm:.6f}")
            if abs(norm - 1.0) > 0.1:  # Allow some tolerance
                logger.warning(
                    f"Embedding {i} has unexpected norm: {norm:.6f} (expected ~1.0)")

        # Convert the embedding data to base64 if requested
        if body.encoding_format == "base64":
            try:
                embedding_data = [
                    base64.b64encode(b.tobytes()).decode('utf-8')
                    for b in embedding_data
                ]
                logger.debug("Base64 encoded embedding data successfully")
            except Exception as e:
                logger.error(
                    f"Error encoding embedding data to base64: {str(e)}")
                raise ValueError(
                    f"Failed to encode embedding data to base64 for model {body.model}") from e
        else:
            # Convert to list of floats for JSON response
            embedding_data = [
                embed.tolist() if isinstance(embed, np.ndarray) else embed
                for embed in embedding_data
            ]

        # Compute usage - estimate tokens based on input text
        prompt_tokens = estimate_tokens(text_input)
        total_tokens = prompt_tokens

        # Prepare embeddings objects
        embeddings = [
            EmbeddingObject(
                object="embedding",
                embedding=embed,
                index=i
            )
            for i, embed in enumerate(embedding_data)
        ]

        usage = EmbeddingUsage(
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens
        )

        embedding_response = EmbeddingResponse(
            object="list",
            data=embeddings,
            model=body.model,
            usage=usage
        )

        # Log usage
        log_embeddings_usage(
            user_id=str(user.id) if user and user.id else "unknown",
            model=body.model,
            prompt_tokens=prompt_tokens,
            input_count=len(text_input),
            request_id=request_id,
            encoding_format=body.encoding_format,
            dimensions=body.dimensions
        )

        logger.info(
            f"Processed Triton embedding request - Model: {body.model}, Inputs: {len(text_input)}, "
            f"Prompt tokens: {prompt_tokens}, Total tokens: {total_tokens}, "
            f"Encoding: {body.encoding_format}, RequestID: {request_id}"
        )

        return embedding_response

    except InferenceServerException as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Triton inference error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Triton embeddings API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in Triton embeddings: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to create embeddings: {str(e)}") from e
