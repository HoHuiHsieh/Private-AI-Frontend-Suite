"""
Request and response models for List models.
Model schemas are designed to be compatible with OpenAI's List models API.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel


class ModelObject(BaseModel):
    """
    OpenAI Model object schema (compatible with /v1/models endpoints).
    https://platform.openai.com/docs/api-reference/models/object
    """
    id: str
    object: Literal["model"] = "model"
    created: Optional[int] = None  # Unix timestamp (seconds)
    owned_by: Optional[str] = None
    # OpenAI docs mention 'permission', 'root', 'parent', but these are not always present
    permission: Optional[list] = None
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelListResponse(BaseModel):
    """
    OpenAI List Models API response schema.
    https://platform.openai.com/docs/api-reference/models/list
    """
    object: Literal["list"] = "list"
    data: List[ModelObject]


# Optionally, you can alias for compatibility
Model = ModelObject
ModelList = ModelListResponse
