# from typing import Any, Dict, Optional
# from datetime import datetime
# from langchain_core.messages import AIMessage, HumanMessage
# from ...models import (
#     ChatAgentStreamDelta,
#     ChatAgentStreamChoice,
#     ChatAgentStreamResponse,
#     ChatAgentUsage
# )


# def extract_streaming_content(last_message: Any) -> tuple[Optional[str], Optional[str]]:
#     """Extract content and reasoning from a message for streaming."""
#     content = getattr(last_message, 'content', None) or None
#     reasoning = getattr(last_message, 'additional_kwargs',
#                         {}).get("reasoning", None)
#     return content, reasoning


# def create_streaming_response(
#     thread_id: str,
#     model_name: str,
#     delta: ChatAgentStreamDelta,
#     usage: Optional[ChatAgentUsage] = None
# ) -> str:
#     """Create a streaming response string."""
#     choice = ChatAgentStreamChoice(index=0, delta=delta)
#     response = ChatAgentStreamResponse(
#         id=thread_id,
#         created=int(datetime.now().timestamp()*1000),
#         model=model_name,
#         choices=[choice],
#         usage=usage,
#     )
#     return f"data: {response.model_dump_json()}\n\n"


# async def handle_chain_stream_event(
#         event: Dict[str, Any],
#         thread_id: str,
#         model_name: str
# ) -> Optional[tuple[str, Optional[str]]]:
#     """Handle on_chain_stream events and return streaming response if applicable."""
#     # Determine the LangGraph node type from metadata
#     langgraph_node = event.get("metadata", {})
#     langgraph_node = langgraph_node.get("langgraph_node")

#     # Extract chunk data
#     chunk_data = event.get("data", {}).get("chunk", {})
#     if not chunk_data or "messages" not in chunk_data:
#         return None, None

#     # Handle specific node types for streaming reasoning
#     if langgraph_node == "ingestion":
#         # Extract messages from chunk data
#         messages = chunk_data["messages"]
#         if not messages or not isinstance(messages, list):
#             return None, None

#         # Extract content and reasoning from the last message
#         last_message = messages[-1]
#         if not isinstance(last_message, HumanMessage):
#             return None, None

#         if "Document file(s) uploaded:" in last_message.content:
#             # Extract reasoning from uploaded file message
#             reasoning = "Document file(s) uploaded.\n----------\n\n"
#             # Create delta for streaming
#             delta = ChatAgentStreamDelta(
#                 role="assistant",
#                 content=None,
#                 reasoning=reasoning
#             )
#             # Return streaming response
#             return create_streaming_response(thread_id, model_name, delta), reasoning

#     elif langgraph_node == "retrieval":
#         # Extract messages from chunk data
#         summarized_messages = chunk_data["summarized_messages"]
#         if not summarized_messages or not isinstance(summarized_messages, list):
#             return None, None

#         # Extract content and reasoning from the last message
#         last_message = summarized_messages[-1]
#         if not isinstance(last_message, HumanMessage):
#             return None, None

#         if "<relevant_documents>" in last_message.content:
#             # Extract reasoning from retrieved document message
#             reasoning = last_message.content.split('<relevant_documents>')[-1]
#             reasoning = reasoning.split('</relevant_documents>')[0]
#             # Create delta for streaming
#             delta = ChatAgentStreamDelta(
#                 role="assistant",
#                 content=None,
#                 reasoning=reasoning
#             )
#             # Return streaming response
#             return create_streaming_response(thread_id, model_name, delta), reasoning

#     return None, None
