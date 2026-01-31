"""
This module initializes LangGraph retrieval  node.
The node is used for retrieving relevant documents based on summarized messages.
"""
from typing import List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_core.messages.utils import merge_message_runs, count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langchain_core.messages.utils import get_buffer_string
from langchain_core.prompts import PromptTemplate
from ..state import State
from .connection import (
    create_chatopenai_connection,
    create_vector_store_connection,
    create_embeddings_connection,
    get_memory_collection_name,
)
from ..utils import estimate_tokens

MAX_INTENT_GUESS_TOKENS = 2000
MAX_RETRIEVAL_TOKENS = 2000


def _guess_intent(chat_model: ChatOpenAI, messages: List[AnyMessage]) -> str:
    """
    Helper function to guess human's intent from messages.
    """
    # Calculate total tokens and find the starting index within limit
    total_tokens = 0
    index = 0
    for i, msg in enumerate(reversed(messages)):
        msg_tokens = estimate_tokens(msg.content)
        if total_tokens + msg_tokens > MAX_INTENT_GUESS_TOKENS:
            break
        total_tokens += msg_tokens
        index = len(messages) - i - 1

    # Get chat history index within token limit
    chat_history = get_buffer_string(messages=messages[index:])

    # Guess human's intent based on chat history, especially the last human message.
    # Respond with a concise search query for retrieval.
    prompt = PromptTemplate(
        input_variables=["history"],
        template=(
            "Given the following conversation history:\n"
            "{history}\n"
            "Determine the human's intent from the most recent human message in the context of this history.\n"
            "Only respond with a short, concise search query (e.g., key phrases or a natural language question) that captures what the user is trying to achieve or ask, suitable for retrieving relevant documents.\n"
            "If no specific intent can be determined, respond with 'none' only."
        ),
    )
    response = chat_model.invoke(prompt.format(history=chat_history))
    if response.content.strip().lower() == "none":
        return None
    return response.content


def retrieval_node(state: State, config: RunnableConfig, **kwargs) -> State:
    """
    Retrieval node to process summarized messages and provide responses.
    """
    # Extract configuration
    model_config = config.get("configurable", {}).get("model", {})
    thread_id = config.get("configurable", {}).get("thread_id")
    api_key = model_config.get("api_key")
    chat_model_name = model_config.get("chat")
    embed_model_name = model_config.get("embed")
    collections = model_config.get("collections", [])

    if not all([thread_id, api_key, chat_model_name, embed_model_name]):
        raise ValueError(
            "Missing required configuration: thread_id, api_key, chat_model_name, or embed_model_name")

    # Extract summarized_messages from state
    summarized_messages = state.get("summarized_messages")
    if not summarized_messages:
        raise ValueError("No messages found in state.")

    summarized_messages = merge_message_runs(summarized_messages)

    # Extract human messages
    last_human_message = summarized_messages[-1]
    if not isinstance(last_human_message, HumanMessage):
        raise ValueError("Last message is not from human.")

    # Extract messages from state
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages found in state.")

    # Create chat model connection
    chat_model = create_chatopenai_connection(
        chat_model_name, api_key)

    # Guess human's intent from messages
    query = _guess_intent(chat_model, messages)
    print(f"\n\nGuessed intent/query for retrieval: {query}")

    # Retrieve relevant documents based on the query
    relevant_docs_content = ""
    if query:
        # Create embedding for the query
        embed_model = create_embeddings_connection(embed_model_name, api_key)
        embedding = embed_model.embed_query(query)

        # Retrieve relevant documents from collections
        relevant_docs = []
        memory_collection = get_memory_collection_name(
            thread_id, embed_model_name)
        for collection_name in [*collections, memory_collection]:
            # Create vector store connection
            vector_store = create_vector_store_connection(
                model_name=embed_model_name,
                api_key=api_key,
                collection_name=collection_name
            )
            # Query vector store for relevant documents
            docs_with_scores = vector_store.similarity_search_with_score_by_vector(
                embedding=embedding, k=20)
            # docs_with_scores = vector_store.similarity_search_with_score(
            #     query=query, k=20)
            # filter out high-score documents
            # docs_with_scores = [item for item in docs_with_scores if item[1] < 0.7]
            # Append to relevant docs list
            relevant_docs.extend(docs_with_scores)

        # Sort relevant documents by score (lower score indicates higher similarity)
        relevant_docs.sort(key=lambda x: x[1])
        # Extract documents from tuples
        relevant_docs = [item[0] for item in relevant_docs]
        # Filter documents to stay within token limit
        filtered_docs = []
        total_tokens = 0
        for doc in relevant_docs:
            doc_tokens = estimate_tokens(doc.page_content)
            if total_tokens + doc_tokens > MAX_RETRIEVAL_TOKENS:
                break
            filtered_docs.append(doc)
            total_tokens += doc_tokens
        relevant_docs = filtered_docs

        # Update relevant documents content in state
        if relevant_docs:
            relevant_docs_content = "\n------\n".join(
                [f"{doc.page_content}\n(Source: {doc.metadata.get('source', 'unknown')})\n" for doc in relevant_docs]
            )
            retrieval_prompt = f"Relevant document(s) found:\n\n{relevant_docs_content}\n\n"
            return {
                **state,
                "prompt": {
                    **state.get("prompt", {}),
                    "retrieval": retrieval_prompt
                }
            }
    # No relevant documents found or no query
    return state
