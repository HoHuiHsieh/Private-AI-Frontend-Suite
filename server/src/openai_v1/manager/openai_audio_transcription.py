# -*- coding: utf-8 -*-
"""OpenAI audio transcription implementation."""
import openai
import httpx
import traceback
import uuid
from typing import Optional
from fastapi import UploadFile
from logger import get_logger
from config import get_config
from .load_balancer import get_load_balancer, build_endpoint_url
from ..models import AudioTranscriptionResponse, AudioTranscriptionUsage
from user import User
from .util import log_transcription_usage


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


async def openai_audio_transcription(
    file: UploadFile,
    model: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: Optional[str] = "json",
    temperature: Optional[float] = None,
    timestamp_granularities: Optional[str] = None,
    api_key: str = "",
    user: User = None
) -> AudioTranscriptionResponse:
    """
    Query audio transcription from OpenAI compatible API server.
    
    Args:
        file: Audio file to transcribe (UploadFile)
        model: Model name for transcription
        language: Language of the audio (ISO-639-1 format, optional)
        prompt: Context to guide transcription (optional)
        response_format: Format of the response (json, text, srt, verbose_json, vtt)
        temperature: Sampling temperature (0-1)
        timestamp_granularities: Comma-separated list (word, segment)
        api_key: API key for backend authentication
        user: User making the request (for usage tracking)
        
    Returns:
        AudioTranscriptionResponse with transcribed text
        
    Raises:
        ValueError: If model is not found in configuration
        RuntimeError: If API call fails
    """
    # Generate request ID for tracking
    request_id = "transcribe-" + str(uuid.uuid4())[:32]

    # Get model configuration
    model_config = config.get_model_config(model)
    if not model_config:
        logger.error(f"Model not found: {model}")
        raise ValueError(f"Model not found: {model}")

    # Select endpoint using load balancer
    lb = get_load_balancer()
    host, port = lb.get_endpoint(model_config.host, model_config.port, model)

    # Mark request start for connection tracking
    lb.mark_request_start(host, port, model)

    try:
        # Read file content
        await file.seek(0)  # Reset file pointer to beginning
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.debug(
            f"Sending transcription request to OpenAI API: model={model}, "
            f"file={file.filename}, size={file_size} bytes"
        )

        # Initialize OpenAI client with backend configuration
        # Skip SSL verification for self-signed certificates
        client = openai.AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=build_endpoint_url(host, port, "/v1"),
            http_client=httpx.AsyncClient(verify=False)
        )

        # Prepare request parameters
        # Note: OpenAI SDK requires a file-like object with name attribute
        request_params = {
            "file": (file.filename, file_content, file.content_type),
            "model": model,
        }
        
        # Add optional parameters
        if language is not None:
            request_params["language"] = language
        if prompt is not None:
            request_params["prompt"] = prompt
        if response_format is not None:
            request_params["response_format"] = response_format
        if temperature is not None:
            request_params["temperature"] = temperature
        if timestamp_granularities is not None:
            # Convert comma-separated string to list
            request_params["timestamp_granularities"] = [
                g.strip() for g in timestamp_granularities.split(",")
            ]

        # Make API call
        response = await client.audio.transcriptions.create(**request_params)

        # Convert OpenAI response to our response model
        # OpenAI SDK returns objects, so we need to access attributes
        
        # Handle different response formats
        if response_format == "json" or response_format == "verbose_json":
            # Response is an object with text and potentially usage
            transcription_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract usage if available
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = AudioTranscriptionUsage(
                    type=response.usage.type if hasattr(response.usage, 'type') else None,
                    input_tokens=response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else None,
                    output_tokens=response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else None,
                    total_tokens=response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None,
                    seconds=response.usage.seconds if hasattr(response.usage, 'seconds') else None
                )
            
            transcription_response = AudioTranscriptionResponse(
                text=transcription_text,
                usage=usage,
                logprobs=response.logprobs if hasattr(response, 'logprobs') else None
            )
        else:
            # For text, srt, vtt formats, response is just text
            transcription_text = str(response)
            transcription_response = AudioTranscriptionResponse(
                text=transcription_text,
                usage=None,
                logprobs=None
            )

        # Mark request as successful
        lb.mark_request_end(host, port, model, success=True)

        # Log usage
        log_transcription_usage(
            user_id=str(user.id) if user and user.id else "unknown",
            model=model,
            request_id=request_id,
            file_name=file.filename,
            file_size=file_size,
            language=language,
            response_format=response_format,
            asr_text=transcription_text,
            text_length=len(transcription_text) if transcription_text else 0,
            usage_data=usage.dict() if usage else None
        )

        logger.info(
            f"Transcription successful - Model: {model}, File: {file.filename}, "
            f"Text length: {len(transcription_text) if transcription_text else 0}"
        )

        return transcription_response

    except ValueError:
        # Re-raise ValueError without wrapping (for validation errors like unsupported format)
        raise
    
    except openai.BadRequestError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, model, success=False)
        
        # Check if it's an unsupported response_format error
        error_message = str(e)
        if "response_format" in error_message and ("not compatible" in error_message or "not supported" in error_message):
            logger.warning(
                f"Unsupported response_format for model '{model}': {error_message}")
            
            # Try to extract the cleaner message from the error
            # Error format: "Error code: 400 - {'error': {'message': '...', ...}}"
            try:
                # Try to extract the message from the error body
                if hasattr(e, 'body') and e.body and 'error' in e.body and 'message' in e.body['error']:
                    clean_message = e.body['error']['message']
                elif "{'error': {'message':" in error_message:
                    # Extract message from string representation
                    import re
                    match = re.search(r"'message':\s*['\"]([^'\"]+)['\"]", error_message)
                    clean_message = match.group(1) if match else f"Model '{model}' does not support the requested response_format"
                else:
                    clean_message = f"Model '{model}' does not support the requested response_format"
            except Exception:
                clean_message = f"Model '{model}' does not support the requested response_format"
            
            raise ValueError(clean_message) from e
        
        logger.error(
            f"OpenAI API bad request error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Audio transcription API error: {str(e)}") from e
    
    except openai.APIError as e:
        # Mark request as failed
        lb.mark_request_end(host, port, model, success=False)
        logger.error(
            f"OpenAI API error: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Audio transcription API error: {str(e)}") from e

    except Exception as e:
        # Mark request as failed
        lb.mark_request_end(host, port, model, success=False)
        logger.error(
            f"Unexpected error in audio transcription: {e}\nTraceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to transcribe audio: {str(e)}") from e