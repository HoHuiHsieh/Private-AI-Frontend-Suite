"""
This module initializes LangGraph ingestion node.
The node is used for preprocessing human inputs with files or documents uploaded.
"""
from typing import List
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langchain_core.messages.utils import merge_message_runs
from langchain_core.documents import Document
from .state import State
import base64
import tempfile
import os
from uuid import uuid4
from typing import List, Union, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from ..connection import create_vector_store_connection, get_memory_collection_name
from ...utils import estimate_tokens

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


def image_loader(image_url: str) -> List[Document]:
    """Load image and return its content as Document objects."""
    # TODO: Implement image loading and OCR logic
    return []


def audio_loader(audio_data: str, audio_format: str) -> List[Document]:
    """Load audio file and return its content as Document objects."""
    # TODO: Implement audio loading and transcription logic
    return []


def file_loader(
        # base64 encoded dataurl string (e.g. "data:application/pdf;base64,JVBERi0xLjcKCjEgMCBvYmoK...")
        file_data: str,
        filename: Optional[str] = None
) -> List[Document]:
    """Load file and return its content as Document objects."""
    if not file_data.startswith('data:'):
        raise ValueError("Invalid dataurl format")

    file_id = uuid4().hex

    # Parse dataurl
    header, b64data = file_data.split(',', 1)
    mime_type = header.split(';')[0].split(':', 1)[1]  # e.g., application/pdf

    # Decode base64 to bytes
    file_bytes = base64.b64decode(b64data)

    # Determine file extension based on mime_type
    if mime_type == 'application/pdf':
        ext = '.pdf'
        loader_class = PyPDFLoader
        kargs = {"mode": "single"}
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ext = '.docx'
        loader_class = Docx2txtLoader
        kargs = {}
    elif mime_type.startswith('text/'):
        # For text files, decode and create document directly
        content = file_bytes.decode('utf-8')
        doc = Document(
            page_content=content,
            metadata={
                'file_id': file_id,
                'source': filename or 'uploaded_file',
                'mime_type': mime_type
            }
        )
        return [doc]
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

        try:
            # Load documents using the appropriate loader
            loader = loader_class(temp_path, **kargs)
            documents = loader.load()

            # Add metadata to each document
            for doc in documents:
                doc.metadata.update({
                    'file_id': file_id,
                    'source': filename or 'uploaded_file',
                    'mime_type': mime_type
                })

            return documents
        finally:
            # Clean up temp file
            os.unlink(temp_path)


def loader_node(state: State, config: RunnableConfig, **kwargs) -> State:
    """
    Loader node to load files/documents from human input messages.
    The loaded documents are then ingested into a vector store memory.
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
                if file_docs:
                    documents.extend(file_docs)

            elif item.get("type") == "image_url":
                image_url = item.get("url", "")
                image_docs = image_loader(image_url)
                if image_docs:
                    documents.extend(image_docs)

            elif item.get("type") == "input_audio":
                audio_file = item.get("input_audio", {})
                audio_data = audio_file.get("data", "")  # Base64 encoded
                audio_format = audio_file.get("format", "")
                audio_docs = audio_loader(audio_data, audio_format)
                if audio_docs:
                    documents.extend(audio_docs)

            elif item.get("type") == "text":
                text_content += item.get("text", "")

            else:
                # Unknown type, skip
                continue

        if documents:
            # Ingest documents into a vector store memory.
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=estimate_tokens
            )
            chunked_docs = text_splitter.split_documents(documents)

            # Add chunks to vector store
            collection_name = get_memory_collection_name(
                thread_id, embed_model_name)
            vector_store = create_vector_store_connection(
                embed_model_name,
                api_key,
                collection_name
            )
            vector_store.add_documents(chunked_docs)

            # Update ingestion summary in state
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
            return {
                **state,
                "messages": [
                    RemoveMessage(id=last_human_message.id),
                    HumanMessage(
                        id=last_human_message.id,
                        content=f"{ingestion_prompt}{text_content}",
                        additional_kwargs=last_human_message.additional_kwargs
                    )
                ],
                "documents": documents
            }

    # No documents to ingest
    return {
        **state,
        "documents": []
    }
