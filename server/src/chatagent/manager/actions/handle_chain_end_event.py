# from typing import Any, Dict, List


# async def handle_chain_end_event(event: Dict[str, Any]) -> List[Any]:
#     """Handle on_chain_end events and extract messages."""

#     output_data = event.get("data", {}).get("output", {})
#     if not output_data or "summarized_messages" not in output_data or "messages" not in output_data:
#         raise ValueError("Missing messages in the end event data")

#     messages = output_data["summarized_messages"] or output_data["messages"]
#     if not messages or not isinstance(messages, list):
#         raise ValueError(
#             "Invalid messages format in the end event data")

#     return messages
