
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Security
from user import User
from apikey import get_current_user_from_api_key
from config import get_config
from ..models import ModelObject, ModelListResponse


# Create router
models_router = APIRouter(tags=["models"])

# Get config
config = get_config()


@models_router.get("/models", response_model=ModelListResponse)
async def list_models(
    user: User = Security(get_current_user_from_api_key)
) -> ModelListResponse:
    """
    List available models
    """
    # Fetch model names from the database or configuration
    model_response_list: List[str, dict] = get_config().get_model_response()
    if not model_response_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No models available"
        )

    # Convert each model dict to ModelObject and return as ModelListResponse
    return ModelListResponse(
        data=[
            ModelObject(**model) if isinstance(model, dict) else model
            for model in model_response_list
        ]
    )
