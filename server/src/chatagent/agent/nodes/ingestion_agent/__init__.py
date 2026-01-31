"""
"""
from langgraph.graph import StateGraph, START, END
from .state import State
from .digest import digest_node
from .loader import loader_node


# Compile graph
workflow = StateGraph(State)
workflow.add_node("loader", loader_node)
workflow.add_node("digest", digest_node)
workflow.add_edge(START, "loader")
workflow.add_edge("loader", "digest")
workflow.add_edge("digest", END)
graph = workflow.compile()


__all__ = ["graph"]
