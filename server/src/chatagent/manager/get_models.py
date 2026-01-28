from typing import List
from langchain_core.messages import HumanMessage, BaseMessage
from logger import get_logger
from config import get_config
from .. import agent
from ..models import (
    ChatAgentModelListResponse,
    ChatAgentSessionResponse,
    SessionData,
)

# Set up logger for this module
logger = get_logger(__name__)


def get_chatagent_models() -> ChatAgentModelListResponse:
    """
    Get available models for the chat agent.
    """
    logger.info("Retrieving available chat agent models")
    model_list = get_config().get_model_response()
    collections = get_config().get_collections()

    # Filter out models whose ID not contains keywords "gpt-5" or "gpt-oss"
    included_model_keywords = {"gpt-5", "gpt-oss", "qwen"}
    filtered_models = [
        model.get("id") for model in model_list
        if any(keyword in model.get("id", "") for keyword in included_model_keywords)
    ]

    # Filter out embeddings whose ID not contains keyword "embed"
    included_embed_keywords = {"embed"}
    filtered_embeds = [
        model.get("id") for model in model_list
        if any(keyword in model.get("id", "") for keyword in included_embed_keywords)
    ]

    # Combine filtered models and embeddings into dict list
    data = {
        "chat": filtered_models,
        "embedding": filtered_embeds,
        "collections": collections
    }
    logger.info(
        f"Returning {len(filtered_models)} chat models and {len(filtered_embeds)} embedding models")
    return ChatAgentModelListResponse(data=data)


async def get_chatagent_sessions(user_id) -> ChatAgentSessionResponse:
    """
    Retrieve all chat sessions for a given user from the checkpointer.

    Args:
        user_id: The user ID to retrieve sessions for

    Returns:
        ChatAgentSessionResponse containing list of user sessions with titles
    """
    # Ensure user_id is a string
    user_id = str(user_id)
    logger.info(f"Retrieving chat agent sessions for user {user_id}")
    sessions: List[SessionData] = []
    seen_session_ids = set()

    # Check if graph and checkpointer are initialized
    if not agent.checkpointer:
        raise RuntimeError("Checkpointer is not initialized.")

    # List all checkpoints (thread_ids) from the checkpointer
    async for cp_tuple in agent.checkpointer.alist(config=None):
        # Extract thread_id from checkpoint metadata
        configurable = cp_tuple.config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        if not thread_id or not isinstance(thread_id, str):
            continue

        # Validate thread_id format and extract session_id
        expected_prefix = f"{user_id}_"
        if not thread_id.startswith(expected_prefix):
            continue

        session_id = thread_id[len(expected_prefix):]
        if not session_id or session_id in seen_session_ids:
            continue

        # Extract title from the first message in the checkpoint
        title = session_id  # Default title is the session_id
        try:
            state = cp_tuple.checkpoint.get("channel_values", {})
            messages = state.get("messages", [])
            if isinstance(messages, list) and len(messages) > 0:
                # Find the last user message
                last_msg = messages[-1]
                if last_msg and isinstance(last_msg.content, str):
                    content = last_msg.content.strip()
                    if content:
                        # Truncate to first 10 words for title
                        words = content.split()
                        if len(words) > 10:
                            title = " ".join(words[:10])[:10] + "..."
                        else:
                            title = content[:10] + "..."
        except Exception as e:
            logger.warning(
                f"Failed to extract title for session {session_id}: {e}")
            # If we can't extract a title, keep the default (session_id)

        # Add session data to the list
        sessions.append(SessionData(
            user_id=user_id,
            session_id=session_id,
            title=title
        ))
        seen_session_ids.add(session_id)

    logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
    return ChatAgentSessionResponse(data=sessions)
