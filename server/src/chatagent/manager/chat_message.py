
from langchain_core.messages import RemoveMessage
from logger import get_logger
from .. import agent
from ..models import (
    ChatMessage
)
from .utils import (
    get_thread_id,
    convert_langchain_message_to_chatmessage,
    convert_chatmessage_to_langchain_message
)


async def get_chat_message(
        user_id: str,
        session_id: str,
        message_id: str
) -> ChatMessage:
    """
    Retrieve a specific chat message by its ID within a session.
    """
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    config = {"configurable": {"thread_id": thread_id}}
    if not agent.checkpointer:
        raise RuntimeError("Graph checkpointer is not initialized.")

    # Checkpoint retrieval
    cp_tuple = await agent.checkpointer.aget_tuple(config)
    if not cp_tuple:
        raise RuntimeError(
            f"No checkpoint found for thread_id: {thread_id}")

    # Extract messages from the checkpoint state
    state = cp_tuple.checkpoint.get("channel_values", {})
    messages = state.get("messages", [])
    if not messages:
        raise RuntimeError(
            f"No messages found for thread_id: {thread_id}")

    # Find the specific message by ID
    for msg in messages:
        if msg.id == message_id:
            return convert_langchain_message_to_chatmessage(msg)

    raise RuntimeError(
        f"Message with ID: {message_id} not found for thread_id: {thread_id}")


async def update_chat_message(
        message: ChatMessage,
        user_id: str,
        session_id: str,
):
    """
    Update a specific chat message by its ID within a session.
    """
    # Check graph initialization
    if not agent.graph:
        raise ValueError("graph must be provided")

    # Update configuration for checkpoint update
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    update_config = {"configurable": {"thread_id": thread_id}}

    # Update the state with the modified message
    update_message = convert_chatmessage_to_langchain_message(message)
    await agent.graph.aupdate_state(update_config, {"messages": [update_message]})


async def delete_chat_message(
        user_id: str,
        session_id: str,
        message_id: str
):
    """
    Delete a specific chat message by its ID within a session.
    """
    print("Deleting message:", message_id, "for session:", session_id)
    # Check graph initialization
    if not agent.graph:
        raise ValueError("graph must be provided")

    # Update configuration for checkpoint update
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    update_config = {"configurable": {"thread_id": thread_id}}

    # Checkpoint retrieval
    cp_tuple = await agent.checkpointer.aget_tuple(update_config)
    if not cp_tuple:
        raise RuntimeError(
            f"No checkpoint found for thread_id: {thread_id}")

    # Extract messages from the checkpoint state
    state = cp_tuple.checkpoint.get("channel_values", {})
    messages = state.get("messages", [])
    if not messages:
        raise RuntimeError(
            f"No messages found for thread_id: {thread_id}")

    # Find index of the message to delete
    delete_index = next((i for i, msg in enumerate(
        messages) if msg.id == message_id), None)
    if delete_index is None:
        raise RuntimeError(
            f"Message with ID: {message_id} not found for thread_id: {thread_id}")

    # Remove messages after the one to delete
    delete_ids = [RemoveMessage(id=msg.id) for msg in messages[delete_index:]]

    # Update the state with the modified message
    await agent.graph.aupdate_state(update_config, {"messages": delete_ids})
