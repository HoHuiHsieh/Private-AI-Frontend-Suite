from logger import get_logger
from config import get_config
from .. import agent
from apikey import ApiKeyManager
from .utils import get_thread_id
from ..models import (
    ChatAgentHistoryResponse,
    ChatAgentRequest,
)
from .get_models import get_chatagent_models
from .utils import (
    get_thread_id,
    convert_langchain_message_to_chatmessage,
    convert_chatmessage_to_langchain_message
)


# Initialize manager
apikey_manager = ApiKeyManager()


async def get_chat_history(user_id: str, session_id: str):
    """
    """
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    config = {"configurable": {"thread_id": thread_id}}
    if not agent.checkpointer:
        raise RuntimeError("Graph checkpointer is not initialized.")

    # Checkpoint retrieval
    cp_tuple = await agent.checkpointer.aget_tuple(config)
    if not cp_tuple:
        return ChatAgentHistoryResponse(data=[])

    # Extract messages from the checkpoint state
    state = cp_tuple.checkpoint.get("channel_values", {})
    messages = state.get("messages", [])
    if not messages:
        return ChatAgentHistoryResponse(data=[])

    # Convert LangChain message objects to ChatMessage objects
    chat_messages = []
    for msg in messages:
        langchain_msg = convert_langchain_message_to_chatmessage(msg)
        chat_messages.append(langchain_msg)

    return ChatAgentHistoryResponse(data=chat_messages)


async def delete_chat_session(user_id: str, session_id: str):
    """
    """
    # Ensure checkpointer is initialized
    if not agent.checkpointer:
        raise RuntimeError("Graph checkpointer is not initialized.")

    # Delete the checkpoint for the specified thread_id
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    await agent.checkpointer.adelete_thread(thread_id)

    # Delete vectorstore
    models = get_chatagent_models()
    embed_models = models.data.get("embedding", [])
    for embed_model in embed_models:
        if embed_model:
            agent.delete_vector_store(
                collection_name=agent.get_memory_collection_name(
                    thread_id, embed_model)
            )


def chat_agent_stream(
        body: ChatAgentRequest,
        user_id: str,
        session_id: str,
        api_key: str
):
    """
    Stream chat responses from the agent.
    """
    print("Starting chat_agent_stream...")
    if not agent.graph:
        raise RuntimeError("Graph is not initialized.")

    # Retrieve thread ID and message details
    thread_id = get_thread_id(user_id=user_id, session_id=session_id)
    messages = body.messages
    chat_model_name = body.model
    embed_model_name = body.additional_kwargs.get("embedding_model")
    collections = body.additional_kwargs.get("collections", [])

    # Stream chat responses
    return agent.stream_chat_responses(
        messages=[convert_chatmessage_to_langchain_message(
            msg) for msg in messages],
        thread_id=thread_id,
        chat_model_name=chat_model_name,
        embed_model_name=embed_model_name,
        collections=collections,
        api_key=api_key
    )

    # config = create_graph_config(thread_id,
    #                              chat_model_name,
    #                              embed_model_name,
    #                              collections,
    #                              api_key)
    # input_data = {
    #     "messages": [
    #         convert_chatmessage_to_langchain_message(msg)
    #         for msg in messages
    #     ],
    #     "usage": ChatAgentUsage(
    #         prompt_tokens=0,
    #         completion_tokens=0,
    #         total_tokens=0
    #     )
    # }

    # # Stream events from graph execution
    # final_reasoning = ""
    # async for event in graph.graph.astream_events(input_data, config, version="v2"):
    #     event_type = event["event"]

    #     if event_type == "on_chain_stream":
    #         # Handle streaming events from graph nodes
    #         streaming_response, reasoning = await handle_chain_stream_event(event, thread_id, body.model)
    #         final_reasoning += reasoning or ""
    #         if streaming_response:
    #             yield streaming_response

    #     elif event_type == "on_chain_end":
    #         # Extract final messages from graph execution
    #         final_state = event.get("data", {}).get("output", {})
    #         final_messages = final_state.get("summarized_messages")

    # # Validate that we have messages to work with
    # if not final_messages:
    #     raise ValueError("No messages received from graph execution")

    # # Create chat model for final streaming
    # chat_model = graph.create_chatopenai_connection(
    #     model_name=body.model,
    #     api_key=api_key
    # )

    # # print("\n\nFinal messages to stream:", final_messages)

    # # Stream final response and accumulate content
    # full_content = ""
    # # reasoning_flag = False
    # async for chunk in chat_model.astream(final_messages):
    #     content = chunk.content
    #     reasoning = None

    #     # Accumulate full content
    #     if content:
    #         full_content += content

    #     # Create streaming delta
    #     delta = ChatAgentStreamDelta(
    #         role="assistant",
    #         content=content,
    #         reasoning=reasoning
    #     )

    #     # Extract usage info if available
    #     usage = None
    #     usage_obj = chunk.usage_metadata
    #     if usage_obj:
    #         usage = ChatAgentUsage(
    #             prompt_tokens=getattr(usage_obj, "prompt_tokens", 0),
    #             completion_tokens=getattr(usage_obj, "completion_tokens", 0),
    #             total_tokens=getattr(usage_obj, "total_tokens", 0)
    #         )

    #     # Yield streaming response
    #     yield create_streaming_response(thread_id, body.model, delta, usage)

    # # Update checkpoint with complete response
    # await update_checkpoint_with_final_message(
    #     thread_id,
    #     chat_model_name,
    #     embed_model_name,
    #     collections,
    #     api_key,
    #     full_content,
    #     final_reasoning
    # )
