from __future__ import annotations

from pathlib import Path
from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import NodeFactory
from .state import RunState


def _route_after_source_lock(state: RunState) -> Literal["pass", "stop"]:
    return "pass" if state.get("source_lock_status") == "PASS" else "stop"


def build_graph(checkpointer=None, repo_root: Path | str | None = None):
    """Build the deterministic ASPAR pre-execution graph.

    When no checkpointer is supplied, an in-memory checkpointer is used. Every
    invocation must still provide a LangGraph thread_id in its config.
    """

    root = Path(repo_root) if repo_root is not None else Path.cwd()
    nodes = NodeFactory(root)

    builder = StateGraph(RunState)
    builder.add_node("intake", nodes.intake)
    builder.add_node("classify", nodes.classify)
    builder.add_node("resolve_role", nodes.resolve_role)
    builder.add_node("resolve_brand", nodes.resolve_brand)
    builder.add_node("source_router", nodes.source_router)
    builder.add_node("retrieve_context", nodes.retrieve_context)
    builder.add_node("validate", nodes.validate)
    builder.add_node("source_lock", nodes.source_lock)
    builder.add_node("plan", nodes.plan)
    builder.add_node("execute", nodes.execute)
    builder.add_node("qa", nodes.qa)
    builder.add_node("writeback", nodes.writeback)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "classify")
    builder.add_edge("classify", "resolve_role")
    builder.add_edge("resolve_role", "resolve_brand")
    builder.add_edge("resolve_brand", "source_router")
    builder.add_edge("source_router", "retrieve_context")
    builder.add_edge("retrieve_context", "validate")
    builder.add_edge("validate", "source_lock")
    builder.add_conditional_edges(
        "source_lock",
        _route_after_source_lock,
        {"pass": "plan", "stop": "writeback"},
    )
    builder.add_edge("plan", "execute")
    builder.add_edge("execute", "qa")
    builder.add_edge("qa", "writeback")
    builder.add_edge("writeback", END)

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Export used by langgraph.json / LangGraph CLI.
graph = build_graph()
