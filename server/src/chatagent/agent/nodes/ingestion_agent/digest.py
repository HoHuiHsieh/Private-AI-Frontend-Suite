"""

"""
from uuid import uuid4
from typing import List, Union, Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .state import State
from ..connection import create_vector_store_connection, create_chatopenai_connection, delete_vector_store
from ...utils import estimate_tokens


DIGEST_CHUNK_SIZE = 2000
DIGEST_CHUNK_OVERLAP = 200
MAX_SUMMARIES_TOKENS = 500
TOP_K = 5

SUMMARIZATION_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="Provide a concise summary of the following text, reducing detail while preserving the key points and main ideas. Respond with the summary directly:\n\n{text}"
)


def _first_level_summarization(chunked_docs: List[Document], api_key: str, chat_model_name: str) -> List[str]:
    """
    Summarize each chunked document to generate initial summaries.
    """
    # Create chat model connection
    model = create_chatopenai_connection(chat_model_name, api_key)
    model.max_tokens = MAX_SUMMARIES_TOKENS

    # Prepare messages for each chunk
    messages = [
        [HumanMessage(content=SUMMARIZATION_PROMPT.format(
            text=doc.page_content))]
        for doc in chunked_docs
    ]

    # Invoke in parallel
    results = model.batch(messages)

    # Return summaries
    summaries = [result.content for result in results]
    return summaries


def _clustered_summarization(chunked_summaries: List[str], api_key: str, chat_model_name: str, embed_model_name: str) -> List[str]:
    """
    Cluster related summaries using vector similarity search and then summarize each cluster.
    """
    # Create temporary vector store for similarity search
    temp_collection = f"temp_cluster_{uuid4().hex}"
    vector_store = create_vector_store_connection(
        embed_model_name, api_key, temp_collection)

    # Add summaries as documents
    docs = [Document(page_content=summary) for summary in chunked_summaries]
    vector_store.add_documents(docs)

    clustered_summaries = []
    remaining_summaries = chunked_summaries.copy()
    group_texts = []

    while remaining_summaries:
        # Take the first remaining summary as seed
        seed_summary = remaining_summaries[0]

        # Find top similar summaries (up to 5 including itself)
        similar_docs = vector_store.similarity_search(
            seed_summary, k=TOP_K)
        group = [
            doc.page_content
            for doc in similar_docs
        ]

        # Remove the group from remaining
        for s in group:
            remaining_summaries.remove(s)

        # Collect group text for batch processing
        combined_text = "\n\n".join(group)
        group_texts.append(combined_text)

    # Batch summarize all groups
    if group_texts:
        model = create_chatopenai_connection(chat_model_name, api_key)
        model.max_tokens = MAX_SUMMARIES_TOKENS
        messages = [
            [HumanMessage(content=SUMMARIZATION_PROMPT.format(text=text))]
            for text in group_texts
        ]
        results = model.batch(messages)
        clustered_summaries = [result.content for result in results]

    # Clean up temporary vector store
    delete_vector_store(temp_collection)

    return clustered_summaries


def _final_summarization(chunked_summaries: List[str], api_key: str, chat_model_name: str) -> str:
    combined_summaries = "\n\n".join(chunked_summaries)
    model = create_chatopenai_connection(chat_model_name, api_key)
    model.max_tokens = MAX_SUMMARIES_TOKENS
    message = HumanMessage(
        content=SUMMARIZATION_PROMPT.format(text=combined_summaries))
    result = model.invoke([message])
    return result.content


def digest_node(state: State, config: RunnableConfig, **kwargs) -> State:
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

    # Extract human messages
    last_human_message = messages[-1]
    if not isinstance(last_human_message, HumanMessage):
        raise ValueError("Last message is not from human.")

    # Extract documents from state
    documents = state.get("documents")

    # If there are no documents, return the state as is
    if documents:
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DIGEST_CHUNK_SIZE,
            chunk_overlap=DIGEST_CHUNK_OVERLAP,
            length_function=estimate_tokens
        )
        chunked_docs = text_splitter.split_documents(documents)

        # First level summarization to each chunk
        chunked_summaries = _first_level_summarization(
            chunked_docs, api_key, chat_model_name)

        # Repeated clustered summarization until token count is small enough
        iteration = 0
        while True:
            estimated_tokens = estimate_tokens(chunked_summaries)
            if estimated_tokens <= DIGEST_CHUNK_SIZE:
                break
            chunked_summaries = _clustered_summarization(
                chunked_summaries, api_key, chat_model_name, embed_model_name)
            iteration += 1
            # Prevent infinite loop
            if iteration > 10:
                break

        # Final summarization to get the digest
        digest = _final_summarization(
            chunked_summaries, api_key, chat_model_name)

        # Update state with the digest
        text_content = last_human_message.content if isinstance(
            last_human_message.content, str) else ""
        return {
            **state,
            "messages": [
                RemoveMessage(id=last_human_message.id),
                HumanMessage(
                    id=last_human_message.id,
                    content=f"Uploaded document(s) digest:\n\n{digest}\n\n-----\n\n{text_content}",
                    additional_kwargs=last_human_message.additional_kwargs
                )
            ],
        }

    return state
