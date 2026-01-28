"""Utility functions for chat completions."""
import json
import uuid
import re
from datetime import datetime
from typing import Optional, Union, List
from usage.utils import log_openai_usage


def log_chat_api_usage(
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_id: Optional[str] = None,
        reasoning_tokens: int = 0,
        cached_tokens: int = 0,
        finish_reason: Optional[str] = None,
        input_count: Optional[int] = None,
        **kwargs
) -> bool:
    """
    Log usage for chat API calls.

    Args:
        user_id: User or API key making the request
        model: Chat model name (e.g., gpt-4, gpt-3.5-turbo)
        prompt_tokens: Number of tokens used in the prompt
        completion_tokens: Number of tokens generated in the completion
        request_id: Optional unique identifier for the request
        reasoning_tokens: Number of tokens used for reasoning (for reasoning models)
        cached_tokens: Number of cached tokens reused from prompt cache
        finish_reason: Reason the model stopped generating (stop, length, tool_calls, etc.)
        input_count: Optional count of input messages
        **kwargs: Additional metadata to log

    Returns:
        bool: True if logging was successful, False otherwise
    """
    # Prepare usage data with all token information
    usage_data = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }

    # Prepare extra data with reasoning tokens, cached tokens, and other metadata
    extra_data_dict = {
        "reasoning_tokens": reasoning_tokens,
        "cached_tokens": cached_tokens,
        "finish_reason": finish_reason,
    }

    # Add any additional kwargs to extra_data
    if kwargs:
        extra_data_dict.update(kwargs)

    # Convert extra_data to JSON string
    extra_data = json.dumps(extra_data_dict)

    # Log using the usage tracking utility
    return log_openai_usage(
        user_id=str(user_id),
        model=model,
        api_type="chat",
        usage_data=usage_data,
        request_id=request_id or str(uuid.uuid4()),
        input_count=input_count,
        extra_data=extra_data
    )


def log_embeddings_usage(
        user_id: str,
        model: str,
        prompt_tokens: int,
        input_count: int,
        request_id: Optional[str] = None,
        encoding_format: str = "float",
        dimensions: Optional[int] = None,
        **kwargs
) -> bool:
    """
    Log usage for embeddings API calls.

    Args:
        user_id: User or API key making the request
        model: Embedding model name (e.g., text-embedding-3-small, text-embedding-3-large)
        prompt_tokens: Number of tokens used in the prompt
        input_count: Number of input texts processed
        request_id: Optional unique identifier for the request
        encoding_format: Encoding format used (float or base64)
        dimensions: Optional dimensions parameter for text-embedding-3 models
        **kwargs: Additional metadata to log

    Returns:
        bool: True if logging was successful, False otherwise
    """
    # Prepare usage data with token information
    usage_data = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": 0,  # Embeddings don't have completion tokens
        "total_tokens": prompt_tokens,
    }

    # Prepare extra data with embeddings-specific metadata
    extra_data_dict = {
        "encoding_format": encoding_format,
        "dimensions": dimensions,
    }

    # Add any additional kwargs to extra_data
    if kwargs:
        extra_data_dict.update(kwargs)

    # Convert extra_data to JSON string
    extra_data = json.dumps(extra_data_dict)

    # Log using the usage tracking utility
    return log_openai_usage(
        user_id=str(user_id),
        model=model,
        api_type="embeddings",
        usage_data=usage_data,
        request_id=request_id or str(uuid.uuid4()),
        input_count=input_count,
        extra_data=extra_data
    )


def estimate_tokens(text: Union[str, List[str]]) -> int:
    """
    Estimate the number of tokens in the input text.
    
    Handles both English and Traditional Chinese text.
    Uses different estimation strategies based on character types:
    - English/ASCII: ~1 token per 4 characters (based on GPT tokenization)
    - Chinese characters (CJK): ~1 token per 1-2 characters
    - Mixed content: Combines both strategies
    
    Args:
        text: Single string or list of strings to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if isinstance(text, list):
        return sum(estimate_tokens(t) for t in text)
    
    if not text:
        return 0
    
    # Count different character types
    # CJK Unified Ideographs (most common Chinese characters)
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
    cjk_chars = len(cjk_pattern.findall(text))
    
    # Count ASCII/Latin characters (excluding spaces)
    ascii_pattern = re.compile(r'[a-zA-Z0-9]')
    ascii_chars = len(ascii_pattern.findall(text))
    
    # Count spaces and punctuation separately
    total_chars = len(text)
    other_chars = total_chars - cjk_chars - ascii_chars
    
    # Token estimation:
    # - CJK characters: ~1.5 tokens per character (conservative estimate)
    # - ASCII words: ~1 token per 4 characters
    # - Other characters (punctuation, spaces): ~1 token per 6 characters
    cjk_tokens = int(cjk_chars * 1.5)
    ascii_tokens = max(1, ascii_chars // 4)
    other_tokens = max(0, other_chars // 6)
    
    total_tokens = cjk_tokens + ascii_tokens + other_tokens
    
    # Ensure at least 1 token for non-empty text
    return max(1, total_tokens)


def log_transcription_usage(
        user_id: str,
        model: str,
        request_id: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        language: Optional[str] = None,
        response_format: Optional[str] = None,
        asr_text: Optional[str] = None,
        text_length: int = 0,
        usage_data: Optional[dict] = None,
        **kwargs
) -> bool:
    """
    Log usage for audio transcription API calls.

    Args:
        user_id: User or API key making the request
        model: Transcription model name (e.g., whisper-1, whisper-large-v3-turbo)
        request_id: Optional unique identifier for the request
        file_name: Name of the audio file
        file_size: Size of the audio file in bytes
        language: Language of the audio
        response_format: Format of the response (json, text, srt, verbose_json, vtt)
        asr_text: Transcribed text content (for accurate token estimation)
        text_length: Length of transcribed text (fallback if asr_text not provided)
        usage_data: Usage statistics from API response
        **kwargs: Additional metadata to log

    Returns:
        bool: True if logging was successful, False otherwise
    """
    # Estimate tokens based on transcribed text using estimate_tokens function
    # This handles both English and Chinese text properly
    if asr_text:
        completion_tokens = estimate_tokens(asr_text)
    else:
        # Fallback to simple estimation if text not provided
        completion_tokens = max(1, text_length // 4) if text_length > 0 else 0
    
    # Override with actual usage data if provided
    if usage_data:
        completion_tokens = usage_data.get('output_tokens', completion_tokens)
    
    # Prepare usage data
    usage_data_dict = {
        "prompt_tokens": 0,  # Audio transcription doesn't have input tokens
        "completion_tokens": completion_tokens,
        "total_tokens": completion_tokens,
    }

    # Prepare extra data with transcription-specific metadata
    extra_data_dict = {
        "file_name": file_name,
        "file_size": file_size,
        "language": language,
        "response_format": response_format,
        "text_length": text_length,
    }
    
    # Add actual usage data if available
    if usage_data:
        extra_data_dict["api_usage"] = usage_data

    # Add any additional kwargs to extra_data
    if kwargs:
        extra_data_dict.update(kwargs)

    # Convert extra_data to JSON string
    extra_data = json.dumps(extra_data_dict)

    # Log using the usage tracking utility
    return log_openai_usage(
        user_id=str(user_id),
        model=model,
        api_type="audio_transcription",
        usage_data=usage_data_dict,
        request_id=request_id or str(uuid.uuid4()),
        input_count=1,  # One audio file
        extra_data=extra_data
    )




__all__ = [
    "log_chat_api_usage",
    "log_embeddings_usage",
    "log_transcription_usage",
    "estimate_tokens"
]
