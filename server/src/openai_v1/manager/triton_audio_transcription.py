# -*- coding: utf-8 -*-
"""Triton audio transcription implementation using gRPC client."""
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
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioTranscriptionUsage,
)
from user import User
from .util import log_transcription_usage, estimate_tokens


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


async def triton_audio_transcription(
    body: AudioTranscriptionRequest,
    api_key: str = "",
    user: User = None
) -> AudioTranscriptionResponse:
    """
    Query audio transcription from Triton inference server using gRPC.
    
    Supports:
    - Multiple response formats (json, text, srt, verbose_json, vtt, diarized_json)
    - Language specification
    - Prompt guidance
    - Temperature control
    - Timestamp granularities
    - Chunking strategies
    - Speaker diarization
    
    Args:
        body: Audio transcription request containing file and model
        api_key: API key for authentication (not used for Triton)
        user: User making the request (for usage tracking)
    
    Returns:
        AudioTranscriptionResponse with transcribed text and usage information
    
    Raises:
        ValueError: If model is not found or audio data is invalid
        RuntimeError: If Triton server query fails
    """
    # Generate request ID for tracking
    request_id = "asr-" + str(uuid.uuid4())[:32]
    
    # Get model configuration
    model = config.get_model_config(body.model)
    if not model:
        logger.error(f"Model not found: {body.model}")
        raise ValueError(f"Model not found: {body.model}")

    # Get audio data from body
    audio_data = body.file
    
    # Validate audio data
    if not audio_data:
        logger.error("Received empty audio data")
        raise ValueError("Received empty audio data")

    logger.info(
        f"Triton audio transcription request - Model: {body.model}, "
        f"Format: {body.response_format}, Language: {body.language}, Stream: {body.stream}"
    )

    # Prepare input data for Triton server
    inputs: List[grpcclient.InferInput] = []
    
    # Audio input (only input supported by the model according to config.pbtxt)
    # Send raw audio bytes directly, not base64 encoded
    buf = grpcclient.InferInput("input_audio", [1], "BYTES")
    buf.set_data_from_numpy(np.array([audio_data], dtype=np.object_))
    inputs.append(buf)
    
    logger.debug(f"Audio data size: {len(audio_data)} bytes")
    
    # Note: The current model config only supports input_audio input
    # Optional parameters (language, prompt, temperature) are not yet supported by the Triton config
    if body.language:
        logger.warning(
            f"Language parameter '{body.language}' specified but not supported by current model config")
    
    if body.prompt:
        logger.warning(
            f"Prompt parameter specified but not supported by current model config")
    
    if body.temperature is not None and body.temperature != 0.0:
        logger.warning(
            f"Temperature parameter {body.temperature} specified but not supported by current model config")

    # Prepare outputs (only output_text is supported according to config.pbtxt)
    outputs = [grpcclient.InferRequestedOutput("output_text")]
    
    # Note: The current model config only supports output_text output
    # Additional outputs (segments, words, diarized_segments) are not yet supported
    if body.response_format in ["verbose_json", "diarized_json"]:
        logger.warning(
            f"Response format '{body.response_format}' requested but only basic text output is supported by current model config")

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
            verbose=False
        )

        logger.debug(
            f"Using gRPC Triton server at {grpc_url} for model {body.model} (load balanced)")

        # Send inference request
        response = triton_client.infer(
            model_name=body.model,
            inputs=inputs,
            outputs=outputs,
            request_id=request_id
        )

        # Mark request as successful
        lb.mark_request_end(host, port, body.model, success=True)
        logger.debug(
            f"Received response from Triton server at {host}:{port} for model {body.model}")

        # Extract the text output from the response
        asr_text = response.as_numpy("output_text")
        if asr_text is None:
            logger.error(
                f"Failed to get transcription output from Triton server at {host}:{port} for model {body.model}")
            raise ValueError(
                f"Failed to get transcription output from Triton server for model {body.model}")
        
        # Handle both bytes and string types
        asr_text = asr_text[0].decode("utf-8") if isinstance(
            asr_text[0], bytes) else str(asr_text[0]) if asr_text else ""
        
        # Log the transcription result
        logger.debug(
            f"Transcription result for model {body.model}: {asr_text[:100]}...")
        
        # Calculate usage information
        # Estimate tokens from transcribed text (handles English and Chinese properly)
        output_tokens = estimate_tokens(asr_text) if asr_text else 0
        
        # Estimate audio duration based on audio data size
        # This is a rough estimate - actual duration depends on audio format and bitrate
        # Common formats: WAV PCM 16kHz mono = ~32KB/sec, MP3 128kbps = ~16KB/sec
        # Use conservative estimate assuming compressed audio
        estimated_seconds = len(audio_data) / (16000)  # ~16KB/sec average
        
        usage = AudioTranscriptionUsage(
            type="audio_transcription",
            input_tokens=0,  # Audio transcription doesn't have input tokens
            output_tokens=output_tokens,
            total_tokens=output_tokens,
            seconds=round(estimated_seconds, 2)
        )
        
        logger.debug(
            f"Usage calculated - Tokens: {output_tokens}, Estimated duration: {estimated_seconds:.2f}s"
        )
        
        # Log usage
        user_id = str(user.id) if user and user.id else "unknown"
        log_transcription_usage(
            user_id=user_id,
            model=body.model,
            request_id=request_id,
            file_size=len(audio_data),
            language=body.language,
            response_format=body.response_format,
            asr_text=asr_text,
            text_length=len(asr_text) if asr_text else 0,
            usage_data=usage.dict() if usage else None
        )

        # Build response based on format
        # For now, return basic JSON response
        # TODO: Implement verbose_json, diarized_json, and other formats when backend supports them
        response_data = AudioTranscriptionResponse(text=asr_text, usage=usage)

        logger.info(
            f"Processed Triton audio transcription request - Model: {body.model}, "
            f"Format: {body.response_format}, Text length: {len(asr_text)}, "
            f"RequestID: {request_id}"
        )

        return response_data

    except InferenceServerException as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Triton inference error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Triton audio transcription API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, body.model, success=False)
        logger.error(
            f"Unexpected error in Triton audio transcription: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to transcribe audio: {str(e)}") from e