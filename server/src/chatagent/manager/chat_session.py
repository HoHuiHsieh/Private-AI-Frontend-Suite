from logger import get_logger
from config import get_config
from .. import agent
from apikey import ApiKeyManager
from .utils import get_thread_id
from ..models import (
    ChatAgentHistoryResponse,
    ChatAgentRequest,
)
from .get_models import get_chatagent_models
from .utils import (
    get_thread_id,
    convert_langchain_message_to_chatmessage,
    convert_chatmessage_to_langchain_message
)


# Initialize manager
apikey_manager = ApiKeyManager()


async def get_chat_history(user_id: str, session_id: str):
    """
    """
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    config = {"configurable": {"thread_id": thread_id}}
    if not agent.checkpointer:
        raise RuntimeError("Graph checkpointer is not initialized.")

    # Checkpoint retrieval
    cp_tuple = await agent.checkpointer.aget_tuple(config)
    if not cp_tuple:
        return ChatAgentHistoryResponse(data=[])

    # Extract messages from the checkpoint state
    state = cp_tuple.checkpoint.get("channel_values", {})
    messages = state.get("messages", [])
    if not messages:
        return ChatAgentHistoryResponse(data=[])

    # Convert LangChain message objects to ChatMessage objects
    chat_messages = []
    for msg in messages:
        langchain_msg = convert_langchain_message_to_chatmessage(msg)
        chat_messages.append(langchain_msg)

    return ChatAgentHistoryResponse(data=chat_messages)


async def delete_chat_session(user_id: str, session_id: str):
    """
    """
    # Ensure checkpointer is initialized
    if not agent.checkpointer:
        raise RuntimeError("Graph checkpointer is not initialized.")

    # Delete the checkpoint for the specified thread_id
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    await agent.checkpointer.adelete_thread(thread_id)

    # Delete vectorstore
    models = get_chatagent_models()
    embed_models = models.data.get("embedding", [])
    for embed_model in embed_models:
        if embed_model:
            agent.delete_vector_store(
                collection_name=agent.get_memory_collection_name(
                    thread_id, embed_model)
            )


def chat_agent_stream(
        body: ChatAgentRequest,
        user_id: str,
        session_id: str,
        api_key: str
):
    """
    Stream chat responses from the agent.
    """
    print("Starting chat_agent_stream...")
    if not agent.graph:
        raise RuntimeError("Graph is not initialized.")

    # Retrieve thread ID and message details
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    messages = body.messages
    chat_model_name = body.model
    embed_model_name = body.additional_kwargs.get("embedding_model")
    collections = body.additional_kwargs.get("collections", [])

    # Stream chat responses
    return agent.stream_chat_responses(
        messages=[convert_chatmessage_to_langchain_message(
            msg) for msg in messages],
        thread_id=thread_id,
        chat_model_name=chat_model_name,
        embed_model_name=embed_model_name,
        collections=collections,
        api_key=api_key
    )
