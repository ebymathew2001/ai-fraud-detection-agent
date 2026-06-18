"""
agent/graph.py
==============
Builds and compiles the LangGraph pipeline.

Imports all node functions from agent/nodes/ (one per file),
wires them in a linear sequence, and exposes get_graph()
which returns a cached compiled graph.

Usage anywhere in the project:
  from agent.graph import get_graph
  result = get_graph().invoke({"transaction_id": "TXN003"})
"""

from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes import (
    load_context,
    analyze_amount,
    analyze_location,
    analyze_merchant,
    search_patterns,
    compute_risk_and_action,
    generate_report,
    save_investigation,
)

# Singleton — compiled once, reused on every API call
_compiled_graph = None

def route_after_load(state: AgentState):           
    if state.get("status") == "error":             
        return END                                 
    return "analyze_amount"                        


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register every node
    graph.add_node("load_context",            load_context)
    graph.add_node("analyze_amount",          analyze_amount)
    graph.add_node("analyze_location",        analyze_location)
    graph.add_node("analyze_merchant",        analyze_merchant)
    graph.add_node("search_patterns",         search_patterns)
    graph.add_node("compute_risk_and_action", compute_risk_and_action)
    graph.add_node("generate_report",         generate_report)
    graph.add_node("save_investigation",      save_investigation)

    # Wire edges — strict linear pipeline, no branching
    graph.add_edge(START,                       "load_context")
    graph.add_conditional_edges("load_context", route_after_load)
    graph.add_edge("analyze_amount",            "analyze_location")
    graph.add_edge("analyze_location",          "analyze_merchant")
    graph.add_edge("analyze_merchant",          "search_patterns")
    graph.add_edge("search_patterns",           "compute_risk_and_action")
    graph.add_edge("compute_risk_and_action",   "generate_report")
    graph.add_edge("generate_report",           "save_investigation")
    graph.add_edge("save_investigation",        END)

    return graph


def get_graph():
    """Return the compiled graph (built once, cached for the app lifetime)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph