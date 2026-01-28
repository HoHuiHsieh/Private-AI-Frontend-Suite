import json
from typing import List, Union
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Request, Depends, Security
from user import User
from apikey import get_current_user_from_api_key
from config import get_config
from logger import get_logger
from ..manager import (
    openai_chat_completion_generator,
    openai_chat_completion,
)
from ..models import (
    ChatCompletionStreamResponse,
    ChatCompletionResponse,
    ChatCompletionRequest
)


# Set up logger for this module
logger = get_logger(__name__)

# Create router
chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post(
    "/completions",
    response_model=Union[ChatCompletionResponse, ChatCompletionStreamResponse]
)
async def chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    user: User = Security(get_current_user_from_api_key)
):
    """
    Create a chat completion.

    This endpoint supports both streaming and non-streaming responses based on the
    `stream` parameter in the request body. Compatible with OpenAI's Chat Completions API.
    """
    # Log the request
    logger.info(
        f"Chat completion request - Model: {body.model}, Messages: {len(body.messages)}, "
        f"Stream: {body.stream}, User: {user.id}"
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
    if target_model.source_type == "openai:chat":
        if body.stream:
            # Streaming response
            stream_generator = openai_chat_completion_generator(
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
            return await openai_chat_completion(
                body,
                api_key=target_model.public_api_key or api_key,
                user=user
            )

    else:
        # Handle unknown model requests
        raise HTTPException(status_code=404, detail="Unknown model")
