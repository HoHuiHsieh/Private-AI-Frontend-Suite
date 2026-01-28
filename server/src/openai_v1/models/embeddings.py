"""
Request and response models for embeddings.
Model schemas are designed to be compatible with OpenAI's Embeddings API.
"""
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """
    OpenAI Embeddings API request schema.
    https://platform.openai.com/docs/api-reference/embeddings/create
    """

    input: Union[str, List[str], List[int], List[List[int]]]
    # input: Union[str, List[str]]
    model: str
    dimensions: Optional[int] = None
    encoding_format: Optional[Literal["float", "base64"]] = "float"
    user: Optional[str] = None


class EmbeddingObject(BaseModel):
    """
    OpenAI Embedding object schema.
    https://platform.openai.com/docs/api-reference/embeddings/object

    Note: embedding can be either a list of floats (default) or a base64-encoded string
    when encoding_format="base64" is specified in the request.
    """

    object: Literal["embedding"] = "embedding"
    # List for float format, str for base64 format
    embedding: Union[List[float], str]
    index: int


class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """
    OpenAI Embeddings API response schema.
    https://platform.openai.com/docs/api-reference/embeddings/create
    """

    object: Literal["list"] = "list"
    data: List[EmbeddingObject]
    model: str
    usage: EmbeddingUsage
