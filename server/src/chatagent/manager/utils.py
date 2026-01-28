import re
from datetime import datetime
from typing import Union
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from uuid_utils import uuid4
from ..models import ChatMessage


def get_thread_id(user_id: str, session_id: str) -> str:
    """
    Generate a unique thread ID for a user session.
    """
    return f"{user_id}_{session_id}"


def convert_chatmessage_to_langchain_message(
        chat_message: ChatMessage
) -> Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]:
    """Convert a ChatMessage to a LangChain message."""
    role = chat_message.role
    content = chat_message.content if chat_message.content is not None else ""

    # Prepare additional_kwargs with all extra fields
    additional_kwargs = chat_message.additional_kwargs.copy(
    ) if chat_message.additional_kwargs else {}
    if chat_message.name:
        additional_kwargs["name"] = chat_message.name
    if chat_message.tool_calls:
        additional_kwargs["tool_calls"] = chat_message.tool_calls
    if chat_message.function_call:
        additional_kwargs["function_call"] = chat_message.function_call
    if chat_message.refusal:
        additional_kwargs["refusal"] = chat_message.refusal
    if chat_message.annotations:
        additional_kwargs["annotations"] = chat_message.annotations
    if not additional_kwargs.get("timestamp"):
        additional_kwargs["timestamp"] = int(datetime.now().timestamp() * 1000)
    if not additional_kwargs.get("reasoning"):
        additional_kwargs["reasoning"] = None

    # Prepare LangChain message id
    msg_id = additional_kwargs.get("id", f"msg-{uuid4().hex}")

    # Create the appropriate LangChain message based on role
    if role == "user":
        return HumanMessage(
            content=content,
            id=msg_id,
            additional_kwargs=additional_kwargs
        )
    elif role == "assistant":
        return AIMessage(
            content=content,
            id=msg_id,
            tool_calls=chat_message.tool_calls,
            additional_kwargs=additional_kwargs
        )
    elif role == "system":
        return SystemMessage(
            content=content,
            id=msg_id,
            additional_kwargs=additional_kwargs
        )
    elif role == "tool":
        # For tool messages, tool_call_id is typically required but may be in additional_kwargs
        tool_call_id = additional_kwargs.pop("tool_call_id", "")
        return ToolMessage(
            content=content,
            id=msg_id,
            tool_call_id=tool_call_id,
            additional_kwargs=additional_kwargs
        )
    elif role == "function":
        # Function role is deprecated, treat as tool message
        return ToolMessage(
            content=content,
            id=msg_id,
            additional_kwargs=additional_kwargs
        )
    elif role == "developer":
        # Developer role treated as system message
        return SystemMessage(
            content=content,
            id=msg_id,
            additional_kwargs=additional_kwargs
        )
    else:
        raise ValueError(f"Unsupported role for conversion: {role}")


def convert_langchain_message_to_chatmessage(
        lc_message: Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]
) -> ChatMessage:
    """Convert a LangChain message to a ChatMessage."""
    role_map = {
        HumanMessage: "user",
        AIMessage: "assistant",
        SystemMessage: "system",
        ToolMessage: "tool"
    }
    role = role_map.get(type(lc_message))
    if not role:
        raise ValueError(
            f"Unsupported LangChain message type: {type(lc_message)}")

    # Prepare additional_kwargs
    additional_kwargs = {}
    if lc_message.additional_kwargs:
        additional_kwargs = lc_message.additional_kwargs.copy()

    additional_kwargs["id"] = lc_message.id or f"msg-{uuid4().hex}"

    # Create and return ChatMessage
    return ChatMessage(
        role=role,
        content=lc_message.content,
        name=getattr(lc_message, 'name', None),
        tool_calls=getattr(lc_message, 'tool_calls', None),
        function_call=getattr(lc_message, 'function_call', None),
        additional_kwargs=additional_kwargs
    )
