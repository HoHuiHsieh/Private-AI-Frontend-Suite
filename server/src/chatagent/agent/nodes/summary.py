"""
This module initializes LangGraph summary node.
The node is used for summarizing long messages into concise summaries.
"""
from langchain_core.messages.utils import merge_message_runs
from langchain_core.runnables import RunnableConfig
from langmem.short_term import summarize_messages
from ..state import State
from .connection import create_chatopenai_connection


MAX_TRIM_TOKENS = 8000
MAX_SUMMARY_TOKENS = 256
MAX_TOKENS = 1000


def summary_node(state: State, config: RunnableConfig, **kwargs) -> State:
    """
    Summary node to summarize long messages into concise summaries.
    """
    # Extract configuration
    model_config = config.get("configurable", {}).get("model", {})
    api_key = model_config.get("api_key")
    chat_model_name = model_config.get("chat")
    if not all([api_key, chat_model_name]):
        raise ValueError(
            "Missing required configuration: api_key, chat_model_name")

    # Extract messages from state
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages found in state.")

    # Summarize messages
    model = create_chatopenai_connection(chat_model_name, api_key)
    summarization_model = model.bind(max_tokens=MAX_SUMMARY_TOKENS)
    summarization_result = summarize_messages(
        messages,
        running_summary=state.get("summary", None),
        model=summarization_model,
        max_tokens=MAX_TOKENS,
        max_summary_tokens=MAX_SUMMARY_TOKENS,
    )
    summarized_messages = merge_message_runs(summarization_result.messages)

    # Update state with summarized messages and summary
    return {
        **state,
        "summarized_messages": summarized_messages,
        "summary": summarization_result.running_summary
    }
