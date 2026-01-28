"""
Audio transcription endpoint.
Handles speech-to-text transcription with OpenAI-compatible API.
"""
from typing import Optional
from fastapi import Request, APIRouter, File, Form, UploadFile, HTTPException, status, Security
from user import User
from apikey import get_current_user_from_api_key
from config import get_config
from logger import get_logger
from ..models import AudioTranscriptionResponse
from ..manager import openai_audio_transcription, triton_audio_transcription


# Set up logger for this module
logger = get_logger(__name__)

# Safely load configuration
try:
    config = get_config()
except Exception as e:
    logger.error(f"Failed to load available models: {e}")
    raise RuntimeError("Configuration loading failed") from e


# Create router
audio_router = APIRouter(prefix="/audio", tags=["audio"])


@audio_router.post("/transcriptions", response_model=AudioTranscriptionResponse)
async def create_transcription(
    request: Request,
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: str = Form(..., description="Model to use for transcription"),
    language: Optional[str] = Form(None, description="Language of the audio (ISO-639-1 format)"),
    prompt: Optional[str] = Form(None, description="Context to guide transcription"),
    response_format: Optional[str] = Form("json", description="Format of the response (json, text, srt, verbose_json, vtt)"),
    temperature: Optional[float] = Form(None, description="Sampling temperature (0-1)"),
    timestamp_granularities: Optional[str] = Form(None, description="Comma-separated list (word, segment)"),
    user: User = Security(get_current_user_from_api_key)
):
    """
    Transcribe audio into the input language.
    
    This endpoint converts audio files to text using speech-to-text models.
    Compatible with OpenAI's Audio Transcriptions API.
    
    Features:
    - Multiple model support (whisper-1, whisper-large-v3-turbo, etc.)
    - Multiple audio formats (mp3, mp4, mpeg, mpga, m4a, wav, webm)
    - Language detection or explicit language specification
    - Prompt-based context for better transcription accuracy
    - Multiple response formats (json, text, srt, verbose_json, vtt)
    - Timestamp granularities (word, segment)
    - Temperature control for randomness
    
    Args:
        file: Audio file to transcribe (required)
        model: Model to use for transcription (required)
        language: Language of the audio (ISO-639-1 format, optional)
        prompt: Context to guide transcription (optional)
        response_format: Format of the response (json, text, srt, verbose_json, vtt)
        temperature: Sampling temperature (0-1)
        timestamp_granularities: Comma-separated list (word, segment)
        user: User object from API key authentication
        
    Returns:
        AudioTranscriptionResponse with transcribed text
        
    Raises:
        HTTPException: If model not found or transcription fails
    """
    # Get model configuration
    model_config = config.get_model_config(model)
    if not model_config:
        logger.error(f"Model not found: {model}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model} not found"
        )
        
    # Get api key from the request
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not api_key:
        logger.error("API key is missing")
        raise HTTPException(status_code=401, detail="API key is missing")
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Get file size for logging
    file_size = 0
    try:
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start
    except Exception as e:
        logger.warning(f"Could not determine file size: {e}")
    
    # Log the request with key information
    logger.info(
        f"Transcription request - Model: {model}, File: {file.filename}, "
        f"Size: {file_size} bytes, Content-Type: {file.content_type}, "
        f"Language: {language}, Format: {response_format}, "
        f"User: {user.id if user else 'unknown'}"
    )
    
    try:
        # Manager function selection based on source_type
        source_type = model_config.source_type
        
        if source_type == "openai:audio:transcription":
            response = await openai_audio_transcription(
                file=file,
                model=model,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                timestamp_granularities=timestamp_granularities,
                api_key=model_config.public_api_key or api_key,
                user=user
            )
        elif source_type == "triton:audio:transcription":
            # Read the audio file to bytes
            await file.seek(0)
            audio_data = await file.read()
            
            # Create request body
            from ..models import AudioTranscriptionRequest
            request_body = AudioTranscriptionRequest(
                file=audio_data,
                model=model,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature or 0.0,
                timestamp_granularities=timestamp_granularities.split(',') if timestamp_granularities else None
            )
            
            response = await triton_audio_transcription(
                body=request_body,
                api_key=api_key,
                user=user
            )
        else:
            logger.error(f"Unsupported source_type for audio transcription: {source_type}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model {model} has unsupported source type: {source_type}"
            )
        
        logger.info(
            f"Transcription successful - Model: {model}, File: {file.filename}, "
            f"User: {user.id if user else 'unknown'}"
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in transcription endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
