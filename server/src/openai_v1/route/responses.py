import json
from typing import Union
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Request, Depends, Security
from user import User
from apikey import get_current_user_from_api_key
from config import get_config
from logger import get_logger
from ..manager import (
    openai_responses_generator,
    openai_responses,
)
from ..models import (
    ResponseRequest,
    ResponseObject,
    StreamingEvent
)


# Set up logger for this module
logger = get_logger(__name__)

# Create router
responses_router = APIRouter(prefix="/responses", tags=["responses"])


@responses_router.post(
    "",
    response_model=Union[ResponseObject, StreamingEvent]
)
async def create_response(
    request: Request,
    body: ResponseRequest,
    user: User = Security(get_current_user_from_api_key)
):
    """
    Create a model response.

    This endpoint supports both streaming and non-streaming responses based on the
    `stream` parameter in the request body. Compatible with OpenAI's Responses API.
    """
    # Log the request
    logger.info(
        f"Response request - Model: {body.model}, "
        f"Stream: {body.stream}, User: {user.id if user else 'None'}"
    )
    logger.debug(
        f"Full request body: {json.dumps(body.model_dump(exclude_none=True), indent=2, ensure_ascii=False)}"
    )

    # Get api key from the request (Security dependency already validated it)
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")

    # Select target model from models with body.model
    target_model = get_config().get_model_config(body.model)
    if not target_model:
        logger.error(f"Model not found: {body.model}")
        raise HTTPException(status_code=404, detail="Model not found")

    # Switch by model source
    if target_model.source_type == "openai:responses":
        if body.stream:
            # Streaming response
            stream_generator = openai_responses_generator(
                body,
                api_key=target_model.public_api_key or api_key,
                user=user
            )
            return StreamingResponse(
                stream_generator,
                media_type="text/event-stream"
            )
        else:
            # Non-streaming response
            return await openai_responses(
                body,
                api_key=target_model.public_api_key or api_key,
                user=user
            )

    else:
        # Handle unknown model requests
        logger.error(
            f"Model source_type '{target_model.source_type}' is not 'openai:responses'")
        raise HTTPException(
            status_code=404, detail=f"Model source type not supported for responses endpoint: {target_model.source_type}")
