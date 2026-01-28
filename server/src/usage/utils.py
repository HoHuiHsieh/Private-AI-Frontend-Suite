"""
Usage tracking utilities

Utilities for tracking and logging API usage from various sources.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database import UsageDB, get_session_factory


def log_openai_usage(
    user_id: str,
    model: str,
    api_type: str,
    usage_data: Dict[str, Any],
    request_id: Optional[str] = None,
    input_count: Optional[int] = None,
    extra_data: Optional[str] = None,
    hostname: Optional[str] = None,
    process_id: Optional[str] = None
) -> bool:
    """
    Log usage data from OpenAI API response to database.
    
    This function accepts OpenAI API usage objects and stores them in the database.
    It extracts token counts from the usage object and creates a usage record.
    
    Args:
        user_id: ID of the user making the request (string format)
        model: Model name (e.g., "gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002")
        api_type: Type of API (e.g., "chat", "completion", "embedding")
        usage_data: OpenAI API usage object containing token counts
                   Example: {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        request_id: Optional unique request identifier
        input_count: Optional count of input items (e.g., number of messages, images)
        extra_data: Optional JSON string with additional metadata
        hostname: Optional hostname where request was processed
        process_id: Optional process ID that handled the request
    
    Returns:
        bool: True if logging was successful, False otherwise
    
    Example:
        >>> from usage.utils import log_openai_usage
        >>> 
        >>> # After making an OpenAI API call
        >>> response = openai.ChatCompletion.create(...)
        >>> 
        >>> log_openai_usage(
        ...     user_id=str(user.id),
        ...     model=response.model,
        ...     api_type="chat",
        ...     usage_data=response.usage.dict(),
        ...     request_id=response.id
        ... )
    """
    try:
        # Extract token counts from usage data
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)
        
        # If total_tokens not available, calculate from prompt + completion
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        
        # Create database session
        SessionLocal = get_session_factory()
        db = SessionLocal()
        
        try:
            # Create usage record
            usage_record = UsageDB(
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
                model=model,
                api_type=api_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_id=request_id,
                input_count=input_count,
                extra_data=extra_data,
                hostname=hostname,
                process_id=process_id,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(usage_record)
            db.commit()
            db.refresh(usage_record)
            
            return True
        
        finally:
            db.close()
    
    except Exception as e:
        # Log the error but don't raise - we don't want usage tracking to break the API
        print(f"Failed to log usage: {e}")
        return False


def log_usage(
    user_id: str,
    model: str,
    api_type: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: Optional[int] = None,
    request_id: Optional[str] = None,
    input_count: Optional[int] = None,
    extra_data: Optional[str] = None,
    hostname: Optional[str] = None,
    process_id: Optional[str] = None
) -> bool:
    """
    Log usage data directly to database (simplified version).
    
    Use this function when you have direct token counts rather than an OpenAI usage object.
    
    Args:
        user_id: ID of the user making the request (string format)
        model: Model name
        api_type: Type of API (e.g., "chat", "completion", "embedding")
        prompt_tokens: Number of prompt tokens (default: 0)
        completion_tokens: Number of completion tokens (default: 0)
        total_tokens: Total token count (if None, calculated from prompt + completion)
        request_id: Optional unique request identifier
        input_count: Optional count of input items
        extra_data: Optional JSON string with additional metadata
        hostname: Optional hostname where request was processed
        process_id: Optional process ID that handled the request
    
    Returns:
        bool: True if logging was successful, False otherwise
    
    Example:
        >>> from usage.utils import log_usage
        >>> 
        >>> log_usage(
        ...     user_id="123",
        ...     model="gpt-4",
        ...     api_type="chat",
        ...     prompt_tokens=100,
        ...     completion_tokens=50,
        ...     request_id="req-abc123"
        ... )
    """
    # Calculate total_tokens if not provided
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens
    
    return log_openai_usage(
        user_id=user_id,
        model=model,
        api_type=api_type,
        usage_data={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        },
        request_id=request_id,
        input_count=input_count,
        extra_data=extra_data,
        hostname=hostname,
        process_id=process_id
    )


async def async_log_openai_usage(
    user_id: str,
    model: str,
    api_type: str,
    usage_data: Dict[str, Any],
    request_id: Optional[str] = None,
    input_count: Optional[int] = None,
    extra_data: Optional[str] = None,
    hostname: Optional[str] = None,
    process_id: Optional[str] = None
) -> bool:
    """
    Async version of log_openai_usage for use in async contexts.
    
    Args:
        Same as log_openai_usage
    
    Returns:
        bool: True if logging was successful, False otherwise
    
    Example:
        >>> from usage.utils import async_log_openai_usage
        >>> 
        >>> await async_log_openai_usage(
        ...     user_id=str(user.id),
        ...     model=response.model,
        ...     api_type="chat",
        ...     usage_data=response.usage.dict(),
        ...     request_id=response.id
        ... )
    """
    # For now, just call the sync version
    # In production, consider using async database operations
    return log_openai_usage(
        user_id=user_id,
        model=model,
        api_type=api_type,
        usage_data=usage_data,
        request_id=request_id,
        input_count=input_count,
        extra_data=extra_data,
        hostname=hostname,
        process_id=process_id
    )


async def async_log_usage(
    user_id: str,
    model: str,
    api_type: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: Optional[int] = None,
    request_id: Optional[str] = None,
    input_count: Optional[int] = None,
    extra_data: Optional[str] = None,
    hostname: Optional[str] = None,
    process_id: Optional[str] = None
) -> bool:
    """
    Async version of log_usage for use in async contexts.
    
    Args:
        Same as log_usage
    
    Returns:
        bool: True if logging was successful, False otherwise
    """
    # Calculate total_tokens if not provided
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens
    
    return await async_log_openai_usage(
        user_id=user_id,
        model=model,
        api_type=api_type,
        usage_data={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        },
        request_id=request_id,
        input_count=input_count,
        extra_data=extra_data,
        hostname=hostname,
        process_id=process_id
    )

