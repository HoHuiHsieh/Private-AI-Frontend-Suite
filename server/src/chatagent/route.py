import traceback
from typing import List, Union
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Request, Depends, Security
from sqlalchemy.orm import Session
from user import get_current_active_user, User
from database import get_session_factory
from logger import get_logger
from apikey.manager import ApiKeyManager
from .manager import (
    get_chatagent_models,
    get_chatagent_sessions,
    get_chat_history,
    chat_agent_stream,
    delete_chat_session,
    get_chat_message,
    update_chat_message,
    delete_chat_message,
)
from .models import (
    ChatAgentModelListResponse,
    ChatAgentSessionResponse,
    ChatAgentHistoryResponse,
    ChatAgentStreamResponse,
    ChatAgentRequest,
    ChatAgentStreamResponse,
    ChatMessage
)
from config import get_config


# Set up logger for this module
logger = get_logger(__name__)

# Initialize router
router = APIRouter()

# Initialize manager
apikey_manager = ApiKeyManager()

# Initialize model list
config = get_config()


def get_db():
    """Get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Chat agent model routes --- #


@router.get("/api/chatagent/models",
            response_model=ChatAgentModelListResponse)
async def get_models_endpoint(
    user: User = Depends(get_current_active_user),
):
    """
    Retrieve available chat agent models.
    """
    try:
        return get_chatagent_models()
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving models")


@router.get("/api/chatagent/sessions",
            response_model=ChatAgentSessionResponse)
async def get_sessions_endpoint(
    user: User = Depends(get_current_active_user),
):
    """
    Retrieve chat sessions for the current user.
    """
    try:
        return await get_chatagent_sessions(user.id)
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error retrieving sessions for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving sessions")

# --- Chat session routes --- #


@router.get("/api/chatagent/chat/{session_id}",
            response_model=ChatAgentHistoryResponse)
async def get_chat_history_endpoint(
    session_id: str,
    user: User = Depends(get_current_active_user),
):
    """
    Retrieve chat history for a specific session.
    """
    try:
        return await get_chat_history(user_id=user.id, session_id=session_id)
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Error retrieving chat history for user {user.id}, session {session_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving chat history")


@router.post("/api/chatagent/chat/{session_id}",
             response_model=ChatAgentStreamResponse)
async def chat_agent_stream_endpoint(
    session_id: str,
    body: ChatAgentRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """ 
    Handle chat interaction with streaming response.
    """
    # Get a available API key with user id
    api_keys = apikey_manager.get_api_keys(db, user.id, False)
    if not api_keys:
        logger.error(f"No available API key for user {user.id}")
        raise HTTPException(status_code=403, detail="No available API key")

    try:
        # Extract the API key string from the ApiKey object
        api_key = api_keys[0].api_key

        # Create streaming response
        return StreamingResponse(
            chat_agent_stream(
                body=body,
                user_id=user.id,
                session_id=session_id,
                api_key=api_key
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in chat agent stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/chatagent/chat/{session_id}")
async def delete_chat_history(
    session_id: str,
    user: User = Depends(get_current_active_user),
):
    """
    Delete chat history for a specific session.
    """
    try:
        await delete_chat_session(user_id=user.id, session_id=session_id)
        return {"detail": "Chat history deleted successfully"}
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Error deleting chat history for user {user.id}, session {session_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error deleting chat history")

# --- Message handling routes --- #


@router.get("/api/chatagent/message/{message_id}/chat/{session_id}")
async def get_chat_message_endpoint(
    session_id: str,
    message_id: str,
    user: User = Depends(get_current_active_user),
):
    """
    Retrieve a specific chat message in a session.
    """
    try:
        return await get_chat_message(user_id=user.id,
                                      session_id=session_id,
                                      message_id=message_id)
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Error retrieving chat message {message_id} for user {user.id}, session {session_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving chat message")


@router.post("/api/chatagent/message/{message_id}/chat/{session_id}")
async def update_chat_message_endpoint(
    session_id: str,
    message_id: str,
    body: ChatMessage,
    user: User = Depends(get_current_active_user),
):
    """
    Update a specific chat message in a session.
    """
    try:
        await update_chat_message(session_id=session_id,
                                  user_id=user.id,
                                  message=body)
        return {"detail": "Chat message updated successfully"}
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Error updating chat message {message_id} for user {user.id}, session {session_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error updating chat message")


@router.delete("/api/chatagent/message/{message_id}/chat/{session_id}")
async def delete_chat_message_endpoint(
    session_id: str,
    message_id: str,
    user: User = Depends(get_current_active_user),
):
    """
    Delete a specific chat message in a session.
    """
    try:
        await delete_chat_message(user_id=user.id,
                                  session_id=session_id,
                                  message_id=message_id)
        return {"detail": "Chat message deleted successfully"}
    except Exception as e:
        traceback.print_exc()
        logger.error(
            f"Error deleting chat message {message_id} for user {user.id}, session {session_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Error deleting chat message")
