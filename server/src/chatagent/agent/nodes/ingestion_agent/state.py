"""
State definition for chatbot graph.
"""
from typing import Annotated, List, Union, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages, AnyMessage
from langchain_core.documents import Document


class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    prompt: Dict[str, str]  # prompt from agentic reasoning for user query
    documents: List[Document]  # ingested documents
