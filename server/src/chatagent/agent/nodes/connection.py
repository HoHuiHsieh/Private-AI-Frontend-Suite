"""Connection utilities for chatbot graph."""
import httpx
from functools import lru_cache
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config import get_config

# Create database connection string
DEFAULT_DATABASE_NAME = "chatbot_db"
db_config = get_config().get_database_config()
DB_URL = db_config.db_connection_string(DEFAULT_DATABASE_NAME)


@lru_cache(maxsize=20)
def create_chatopenai_connection(model_name: str, api_key: str):
    """
    Create a connection to the ChatOpenAI service with caching.

    This function caches connections based on model_name and api_key to avoid
    recreating connections for the same parameters.

    Args:
        model_name: The name of the chat model to use
        api_key: The API key for authentication

    Returns:
        ChatOpenAI: Configured chat model instance
    """
    return ChatOpenAI(
        model=model_name,
        base_url='http://localhost:3000/v1',
        api_key=api_key,
        http_client=httpx.Client(verify=False),
        streaming=False,
        timeout=300.0,
        max_retries=2,
    )


@lru_cache(maxsize=20)
def create_embeddings_connection(model_name: str, api_key: str):
    """
    Create a connection to the embeddings service with caching.

    Args:
        model_name: The name of the embedding model to use
        api_key: The API key for authentication

    Returns:
        OpenAIEmbeddings: Configured embeddings instance
    """
    return OpenAIEmbeddings(
        model=model_name,
        base_url='http://localhost:3000/v1',
        api_key=api_key,
        http_client=httpx.Client(verify=False),
        timeout=300.0,
        max_retries=2,
        tiktoken_enabled=False,
        check_embedding_ctx_length=False
    )


@lru_cache(maxsize=20)
def create_vector_store_connection(
        model_name: str,
        api_key: str,
        collection_name: str
):
    """
    Create a connection to the vector store with caching.

    This function caches vector store connections to improve performance
    when the same collection is accessed multiple times.

    Args:
        model_name: The name of the embedding model
        api_key: The API key for authentication
        collection_name: The name of the vector store collection

    Returns:
        PGVector: Configured vector store instance
    """
    embeddings = create_embeddings_connection(model_name, api_key)
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=DB_URL,
        use_jsonb=True,
    )

@lru_cache(maxsize=20)
def create_checkpointer() -> AsyncPostgresSaver:
    """Create a checkpointer instance."""
    return AsyncPostgresSaver.from_conn_string(DB_URL)


def delete_vector_store(collection_name: str):
    """Delete a vector store collection."""
    pg_vector = PGVector(
        embeddings=None,
        collection_name=collection_name,
        connection=DB_URL,
        use_jsonb=True,
    )
    pg_vector.delete_collection()


def get_memory_collection_name(thread_id: str, embed_model_id: str) -> str:
    """Generate collection name for vector store."""
    return f'mem_{thread_id}_{embed_model_id}'


__all__ = [
    "create_chatopenai_connection",
    "create_vector_store_connection",
    "delete_vector_store",
    "get_memory_collection_name",
    "create_checkpointer",
]
