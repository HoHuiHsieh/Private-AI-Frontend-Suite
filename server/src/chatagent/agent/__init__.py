"""
Chatbot graph nodes and workflow definition.
"""
from datetime import datetime
from uuid import uuid4
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, RemoveMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import List
from ..models import (
    ChatAgentStreamDelta,
    ChatAgentStreamChoice,
    ChatAgentStreamResponse,
    ChatAgentUsage
)
from .nodes import (
    ingestion_node,
    ingestion_agent_graph,
    retrieval_node,
    summary_node,
    delete_vector_store,
    get_memory_collection_name,
    create_chatopenai_connection,
    create_checkpointer
)
from .state import State


checkpointer_ctx = None
checkpointer = None
graph = None


async def initialize_chatagent():
    """Initialize chatbot graph and checkpointer."""
    global checkpointer, graph, checkpointer_ctx

    if checkpointer is None or checkpointer_ctx is None:
        # Initialize checkpointer
        checkpointer_ctx = create_checkpointer()
        checkpointer = await checkpointer_ctx.__aenter__()
        try:
            await checkpointer.setup()
            print("Chatbot checkpointer schema setup completed.")
        except Exception as setup_error:
            # If setup fails due to existing schema, continue
            if "already exists" in str(setup_error):
                print("Chatbot checkpointer schema already exists, skipping setup.")
            else:
                raise

    if graph is None:
        # Compile graph
        workflow = StateGraph(State)
        # workflow.add_node("ingestion", ingestion_node)
        workflow.add_node("ingestion", ingestion_agent_graph)
        workflow.add_node("summary", summary_node)
        workflow.add_node("retrieval", retrieval_node)
        workflow.add_edge(START, "ingestion")
        workflow.add_edge("ingestion", "summary")
        workflow.add_edge("summary", "retrieval")
        workflow.add_edge("retrieval", END)
        graph = workflow.compile(checkpointer=checkpointer)


async def stream_chat_responses(
    messages: List[AnyMessage],
    thread_id: str,
    chat_model_name: str,
    embed_model_name: str,
    collections: List[str],
    api_key: str
):
    """
    Stream chat responses from the agent.
    """
    if graph is None:
        raise RuntimeError("Graph is not initialized.")

    # Create graph config
    input_config = {
        "configurable": {
            "thread_id": thread_id,
            "model": {
                "chat": chat_model_name,
                "embed": embed_model_name,
                "api_key": api_key,
                "collections": collections,
            }
        },
        "recursion_limit": 5,
    }

    # Create input state
    input_state = {
        "messages": messages,
        "prompt": {
            "ingestion": "",
            "retrieval": ""
        },
        "summarized_messages": [],
    }

    # Stream events from graph execution
    final_reasoning = None
    summarized_messages = None
    async for event in graph.astream_events(input_state, input_config, version="v2"):
        event_type = event["event"]

        if event_type == "on_chain_stream":
            # Determine the LangGraph node type from metadata
            langgraph_node = event.get("metadata", {})
            langgraph_node = langgraph_node.get("langgraph_node")

            # Extract chunk data
            chunk_data = event.get("data", {}).get("chunk", {})
            if not chunk_data or "messages" not in chunk_data:
                continue

            # Handle specific node types for streaming reasoning
            if langgraph_node == "ingestion":
                # Extract reasoning from chunk data
                reasoning = chunk_data.get("prompt", {}).get("ingestion")
            elif langgraph_node == "retrieval":
                # Extract reasoning from chunk data
                reasoning = chunk_data.get("prompt", {}).get("retrieval")
            else:
                continue

            # Response reasoning if available
            if reasoning:
                # Create delta for streaming
                delta = ChatAgentStreamDelta(
                    role="assistant",
                    content=None,
                    reasoning=reasoning
                )
                # Response streaming
                response = ChatAgentStreamResponse(
                    id=thread_id,
                    created=int(datetime.now().timestamp()*1000),
                    model=chat_model_name,
                    choices=[ChatAgentStreamChoice(index=0, delta=delta)],
                    usage=None,
                )
                yield f"data: {response.model_dump_json()}\n\n"

        elif event_type == "on_chain_end":
            # Extract final state from graph execution
            final_state = event.get("data", {}).get("output", {})

            # Extract the original messages from final state (make a copy to avoid modifying)
            original_messages = [
                msg for msg in final_state.get("messages", [])]

            # Extract summarized messages from graph execution
            summarized_messages = final_state.get("summarized_messages")
            if not summarized_messages:
                continue

            # Extract final prompt from graph execution
            final_prompt = final_state.get("prompt", {})

            # Extract last human message content
            if not isinstance(summarized_messages[-1], HumanMessage):
                raise ValueError("Last message is not a HumanMessage")

            human_msg_content = summarized_messages[-1].content

            # Re-format last human message (create a new message to avoid modifying original)
            formatted_human_msg = HumanMessage(
                content=PromptTemplate(
                    input_variables=["ingestion", "retrieval", "content"],
                    template=(
                        "{retrieval}\n\n"
                        "{content}"
                    ),
                ).format(
                    **final_prompt,
                    content=human_msg_content
                ).strip(),
                additional_kwargs=summarized_messages[-1].additional_kwargs
            )

            # Replace the last message in summarized_messages with the formatted version
            summarized_messages = summarized_messages[:-
                                                      1] + [formatted_human_msg]

            # Format final reasoning
            final_reasoning = PromptTemplate(
                input_variables=["ingestion", "retrieval"],
                template=(
                    "{ingestion}\n\n"
                    "{retrieval}"
                ),
            ).format(**final_prompt).strip()

    # Validate that we have messages to work with
    if not summarized_messages:
        raise ValueError("No messages received from graph execution")

    # Create chat model for final streaming
    chat_model = create_chatopenai_connection(
        model_name=chat_model_name,
        api_key=api_key
    )

    # print("\n\n", summarized_messages, "\n\n")
    # Stream final response and accumulate content
    full_content = ""
    async for chunk in chat_model.astream(summarized_messages):
        content = chunk.content

        # Accumulate full content
        if content:
            full_content += content

        # Create streaming delta
        delta = ChatAgentStreamDelta(
            role="assistant",
            content=content,
            reasoning=None
        )

        # Extract usage info if available
        usage = None
        usage_obj = chunk.usage_metadata
        if usage_obj:
            usage = ChatAgentUsage(
                prompt_tokens=getattr(usage_obj, "prompt_tokens", 0),
                completion_tokens=getattr(usage_obj, "completion_tokens", 0),
                total_tokens=getattr(usage_obj, "total_tokens", 0)
            )

        # Response streaming
        response = ChatAgentStreamResponse(
            id=thread_id,
            created=int(datetime.now().timestamp()*1000),
            model=chat_model_name,
            choices=[ChatAgentStreamChoice(index=0, delta=delta)],
            usage=usage,
        )
        yield f"data: {response.model_dump_json()}\n\n"

    # Check if full content is available
    if not full_content:
        raise ValueError("Full content must be provided")

    # Update the original messages with the final response
    current_timestamp = int(datetime.now().timestamp() * 1000)
    last_message = original_messages[-1]
    updated_messages = None
    if isinstance(last_message, AIMessage):
        updated_messages = [
            RemoveMessage(id=last_message.id),
            AIMessage(
                id=last_message.id,
                content=full_content,
                additional_kwargs={
                    **last_message.additional_kwargs,
                    "timestamp": current_timestamp,
                    "reasoning": final_reasoning
                }
            )
        ]
    elif isinstance(last_message, HumanMessage):
        updated_messages = [AIMessage(
            id=f"msg-{uuid4().hex}",
            content=full_content,
            additional_kwargs={
                "id": f"msg_{current_timestamp}",
                "reasoning": final_reasoning,
                "timestamp": current_timestamp
            }
        )]
    else:
        raise ValueError("Last message is neither AIMessage nor HumanMessage")

    # Update the state with the modified message
    await graph.aupdate_state({
        "configurable": {"thread_id": thread_id}
    }, {
        "messages": updated_messages
    })


__all__ = [
    "initialize_chatagent",
    "stream_chat_responses",
    "delete_vector_store",
    "get_memory_collection_name",
]
