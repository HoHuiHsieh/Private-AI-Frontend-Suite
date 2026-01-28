import json
from fastapi import APIRouter, HTTPException, Request, Security
from user import User
from apikey import get_current_user_from_api_key
from config import get_config
from logger import get_logger
from ..manager import (
    openai_embeddings,
    triton_embeddings,
)
from ..models import (
    EmbeddingRequest,
    EmbeddingResponse
)


# Set up logger for this module
logger = get_logger(__name__)

# Create router
embeddings_router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@embeddings_router.post("", response_model=EmbeddingResponse)
@embeddings_router.post("/", response_model=EmbeddingResponse)
async def embeddings(
    request: Request,
    body: EmbeddingRequest,
    user: User = Security(get_current_user_from_api_key)
):
    """
    Create embeddings for the provided input.

    This endpoint converts text into vector embeddings using the specified model.
    Compatible with OpenAI's Embeddings API.
    """
    # Log the request
    input_count = len(body.input) if isinstance(body.input, list) else 1
    logger.info(
        f"Embeddings request - Model: {body.model}, Inputs: {input_count}, "
        f"Format: {body.encoding_format}, Dimensions: {body.dimensions}, "
        f"User: {user.id}"
    )
    logger.debug(
        f"Full request body: {json.dumps(body.model_dump(exclude_none=True), indent=2, ensure_ascii=False)}"
    )

    # Get api key from the request
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not api_key:
        logger.error("API key is missing")
        raise HTTPException(status_code=401, detail="API key is missing")

    # Select target model from models with body.model
    target_model = get_config().get_model_config(body.model)
    if not target_model:
        logger.error(f"Model not found: {body.model}")
        raise HTTPException(status_code=404, detail="Model not found")

    # Switch by model source
    if target_model.source_type == "triton:embeddings":
        return await triton_embeddings(
            body,
            api_key=target_model.public_api_key or api_key,
            user=user
        )
    elif target_model.source_type == "openai:embeddings":
        # Non-streaming response
        return await openai_embeddings(
            body,
            api_key=target_model.public_api_key or api_key,
            user=user
        )

    else:
        # Handle unknown model requests
        raise HTTPException(status_code=404, detail="Unknown model")
