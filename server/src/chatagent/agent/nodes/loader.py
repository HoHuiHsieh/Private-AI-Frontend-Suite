import base64
import tempfile
import os
from uuid import uuid4
from typing import List, Union, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from .connection import create_vector_store_connection, get_memory_collection_name

CHUNK_SIZE = 1000
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
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ext = '.docx'
        loader_class = Docx2txtLoader
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
        loader = loader_class(temp_path)
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


def ingestion_to_memory(
        documents: List[Document],
        embed_model_name: str,
        api_key: str,
        thread_id: str
):
    """
    Ingest documents into a vector store memory.
    """
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunked_docs = text_splitter.split_documents(documents)

    # Add chunks to vector store
    collection_name = get_memory_collection_name(thread_id, embed_model_name)
    vector_store = create_vector_store_connection(
        embed_model_name,
        api_key,
        collection_name
    )
    vector_store.add_documents(chunked_docs)
