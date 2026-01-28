"""
Request and response models for audio transcription.
Model schemas are designed to be compatible with OpenAI's Audio Transcription API.
"""
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

class AudioTranscriptionRequest(BaseModel):
    """
    OpenAI Audio Transcription API request schema.
    https://platform.openai.com/docs/api-reference/audio/createTranscription
    """
    file: bytes  # In FastAPI, use UploadFile, but for schema, bytes
    model: str
    chunking_strategy: Optional[Union[str, dict]] = None
    include: Optional[List[str]] = None
    known_speaker_names: Optional[List[str]] = None
    known_speaker_references: Optional[List[str]] = None
    language: Optional[str] = None
    prompt: Optional[str] = None
    response_format: Optional[str] = "json"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.0
    timestamp_granularities: Optional[List[str]] = None

class AudioTranscriptionUsage(BaseModel):
    type: Optional[str] = None
    input_tokens: Optional[int] = None
    input_token_details: Optional[dict] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    seconds: Optional[float] = None

class AudioTranscriptionResponse(BaseModel):
    """
    OpenAI Audio Transcription API response schema (JSON).
    https://platform.openai.com/docs/api-reference/audio/json-object
    """
    text: str
    usage: Optional[AudioTranscriptionUsage] = None
    logprobs: Optional[list] = None

# Diarized and verbose JSON responses are more complex; add as needed.

# Streaming events (for stream=True)
class TranscriptTextDeltaEvent(BaseModel):
    type: Literal["transcript.text.delta"] = "transcript.text.delta"
    delta: str
    logprobs: Optional[list] = None
    segment_id: Optional[str] = None

class TranscriptTextDoneEvent(BaseModel):
    type: Literal["transcript.text.done"] = "transcript.text.done"
    text: str
    usage: Optional[AudioTranscriptionUsage] = None
    logprobs: Optional[list] = None

class TranscriptTextSegmentEvent(BaseModel):
    type: Literal["transcript.text.segment"] = "transcript.text.segment"
    id: str
    start: float
    end: float
    text: str
    speaker: Optional[str] = None

