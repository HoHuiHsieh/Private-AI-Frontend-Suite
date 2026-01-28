"""
This module initializes LangGraph ingestion node.
The node is used for preprocessing human inputs with files or documents uploaded.
"""
from typing import List
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langchain_core.messages.utils import merge_message_runs
from langchain_core.documents import Document
from .loader import (
    image_loader,
    audio_loader,
    file_loader,
    ingestion_to_memory
)
from ..state import State


def ingestion_node(state: State, config: RunnableConfig, **kwargs) -> State:
    """
    Ingestion node to add documents to the state from human inputs.
    """
    # Extract configuration
    model_config = config.get("configurable", {}).get("model", {})
    thread_id = config.get("configurable", {}).get("thread_id")
    api_key = model_config.get("api_key")
    chat_model_name = model_config.get("chat")
    embed_model_name = model_config.get("embed")
    if not all([thread_id, api_key, chat_model_name, embed_model_name]):
        raise ValueError(
            "Missing required configuration: thread_id, api_key, chat_model_name, or embed_model_name")

    # Extract messages from state
    messages = state.get("messages")
    if not messages:
        raise ValueError("No messages found in state.")

    messages = merge_message_runs(messages)

    # Extract human messages
    last_human_message = messages[-1]
    if not isinstance(last_human_message, HumanMessage):
        raise ValueError("Last message is not from human.")

    # Skip if no documents to ingest in the last_human_message
    ingestion_prompt = ""
    if isinstance(last_human_message.content, list):
        # Assume documents are in the content of the last human message,
        # which can be a mix of text, files, image URLs, etc.
        text_content = ""
        documents: List[Document] = []
        for item in last_human_message.content:
            # Handle plain text items
            if isinstance(item, str):
                continue

            # Create Document objects based on item type
            if item.get("type") == "file":
                doc_file = item.get("file", {})
                file_data = doc_file.get("file_data", "")  # Base64 encoded
                file_name = doc_file.get("file_name", "unknown")
                file_docs = file_loader(file_data, file_name)
                documents.extend(file_docs)

            elif item.get("type") == "image_url":
                image_url = item.get("url", "")
                image_docs = image_loader(image_url)
                documents.extend(image_docs)

            elif item.get("type") == "input_audio":
                audio_file = item.get("input_audio", {})
                audio_data = audio_file.get("data", "")  # Base64 encoded
                audio_format = audio_file.get("format", "")
                audio_docs = audio_loader(audio_data, audio_format)
                documents.extend(audio_docs)

            elif item.get("type") == "text":
                text_content += item.get("text", "")

            else:
                # Unknown type, skip
                continue

        # Ingest documents into a vector store memory.
        ingestion_to_memory(
            documents,
            embed_model_name,
            api_key,
            thread_id
        )

        # Update ingestion summary in state
        if documents:
            unique_files = set()
            doc_lines = []
            for doc in documents:
                filename = doc.metadata.get('source', 'uploaded_file')
                filetype = doc.metadata.get('mime_type', 'unknown_type')
                if filename in unique_files:
                    continue
                unique_files.add(filename)
                doc_lines.append(f"- {filename} ({filetype})")

            ingestion_prompt = f"Document file(s) uploaded:\n{'\n'.join(doc_lines) or 'none'}\n----------\n"

            # Update the last human message content to only the text parts
            updated_human_message = HumanMessage(
                id=last_human_message.id,
                content=f"{ingestion_prompt}{text_content}",
                additional_kwargs=last_human_message.additional_kwargs
            )
            return {
                **state,
                "messages": [
                    RemoveMessage(id=last_human_message.id),
                    updated_human_message
                ],
                "prompt": {
                    **state.get("prompt", {}),
                    "ingestion": ingestion_prompt
                }
            }
    # No documents to ingest, return state as is
    return state
