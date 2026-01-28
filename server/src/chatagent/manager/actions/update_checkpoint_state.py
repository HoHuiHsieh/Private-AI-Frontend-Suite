# from typing import Any, Dict, Optional
# from datetime import datetime
# from uuid import uuid4
# from langchain_core.messages import AIMessage, BaseMessage
# from langgraph.graph.state import CompiledStateGraph
# from ... import graph


# def create_graph_config(
#         thread_id: str,
#         chat_model: str,
#         embed_model: str,
#         collections: list[str],
#         api_key: str
# ) -> Dict[str, Any]:
#     """Create configuration for the graph execution."""
#     return {
#         "configurable": {
#             "thread_id": thread_id,
#             "model": {
#                 "chat": chat_model,
#                 "embed": embed_model,
#                 "api_key": api_key,
#                 "collections": collections,
#             }
#         },
#         "recursion_limit": 5,
#     }


# async def update_checkpoint_with_final_message(
#     thread_id: str,
#     model_name: str,
#     embed_model_name: str,
#     collections: list[str],
#     api_key: str,
#     full_content: str,
#     reasoning: Optional[str] = None,
# ) -> None:
#     """Update the last message in the graph checkpoint with the complete response content."""
#     if not graph.graph:
#         raise ValueError("graph must be provided")

#     if not full_content:
#         raise ValueError("Full content must be provided")

#     # Update configuration for checkpoint update
#     update_config = create_graph_config(
#         thread_id, model_name, embed_model_name, collections, api_key)

#     # Update the checkpoint with the final message
#     # Get the current state
#     current_state = await graph.graph.aget_state(update_config)

#     if not current_state or not current_state.values:
#         raise ValueError("No current state found")

#     # Get messages from current state
#     messages: list[BaseMessage] = current_state.values.get("messages", [])
#     if not messages:
#         raise ValueError("No messages to update")

#     # Get the last message and update its content
#     current_timestamp = int(datetime.now().timestamp() * 1000)
#     last_message = messages[-1]
#     if isinstance(last_message, AIMessage):
#         last_message.content = full_content
#         last_message.additional_kwargs["timestamp"] = current_timestamp
#     else:
#         last_message = AIMessage(
#             id=f"msg-{uuid4().hex}",
#             content=full_content,
#             additional_kwargs={
#                 "id": f"msg_{current_timestamp}",
#                 "reasoning": reasoning,
#                 "timestamp": current_timestamp
#             }
#         )

#     # Update the state with the modified message
#     await graph.graph.aupdate_state(update_config, {"messages": [last_message]})
