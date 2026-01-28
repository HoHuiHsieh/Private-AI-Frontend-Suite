"""
State definition for chatbot graph.
"""
from typing import Annotated, List, Union, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages, AnyMessage
from langmem.short_term import RunningSummary


class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]  # messages between user and assistant
    prompt: Dict[str, str]  # prompt from agentic reasoning for user query
    summary: RunningSummary  # summary of conversation (langmem)
    summarized_messages: List[AnyMessage]  # messages that have been summarized (langmem)
