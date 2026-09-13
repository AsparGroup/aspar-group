"""Graph for the ASPAR feasibility study pipeline — codifies the "Méthode"
doctrine's 7-phase gate chain that was previously tracked manually in
Notion (Laboratoire/Radar). Each phase is a conditional edge: PASS moves
to the next phase, STOP routes to `block` and the run ends there.

Phase 7 (CEO gate) is a genuine human-in-the-loop interrupt — the graph
pauses and must be resumed with `ceo_decision` set explicitly. It never
assumes a decision.
"""

from __future__ import annotations

from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .study_nodes import StudyNodeFactory
from .study_state import StudyState


def _route(state: StudyState) -> Literal["pass", "stop"]:
    results = state.get("phase_results", [])
    if not results:
        return "stop"
    return "pass" if results[-1].get("status") == "PASS" else "stop"


def _ceo_gate_with_interrupt(nodes: StudyNodeFactory):
    def _node(state: StudyState) -> dict:
        if not state.get("ceo_decision"):
            interrupt(
                {
                    "reason": "Phase 7 — Gate GO étude approfondie : décision humaine requise.",
                    "concept_name": state.get("concept_name", ""),
                }
            )
        return nodes.phase_ceo_gate(state)

    return _node


def build_study_graph(checkpointer=None):
    """Build the deterministic ASPAR feasibility-study gate (7 phases)."""

    nodes = StudyNodeFactory()

    builder = StateGraph(StudyState)
    builder.add_node("phase_sourcing", nodes.phase_sourcing)
    builder.add_node("phase_dimensionnement", nodes.phase_dimensionnement)
    builder.add_node("generate_3d_visualization", nodes.generate_3d_visualization)
    builder.add_node("phase_capex", nodes.phase_capex)
    builder.add_node("phase_tarification", nodes.phase_tarification)
    builder.add_node("phase_score_marche", nodes.phase_score_marche)
    builder.add_node("phase_preuves", nodes.phase_preuves)
    builder.add_node("phase_ceo_gate", _ceo_gate_with_interrupt(nodes))
    builder.add_node("block", nodes.block)

    builder.add_edge(START, "phase_sourcing")
    builder.add_conditional_edges(
        "phase_sourcing", _route, {"pass": "phase_dimensionnement", "stop": "block"}
    )
    builder.add_conditional_edges(
        "phase_dimensionnement", _route, {"pass": "generate_3d_visualization", "stop": "block"}
    )
    # Le rendu 3D est un livrable, pas un gate — succès ou échec, l'étude continue.
    builder.add_edge("generate_3d_visualization", "phase_capex")
    builder.add_conditional_edges(
        "phase_capex", _route, {"pass": "phase_tarification", "stop": "block"}
    )
    builder.add_conditional_edges(
        "phase_tarification", _route, {"pass": "phase_score_marche", "stop": "block"}
    )
    builder.add_conditional_edges(
        "phase_score_marche", _route, {"pass": "phase_preuves", "stop": "block"}
    )
    builder.add_conditional_edges(
        "phase_preuves", _route, {"pass": "phase_ceo_gate", "stop": "block"}
    )
    builder.add_conditional_edges(
        "phase_ceo_gate", _route, {"pass": END, "stop": "block"}
    )
    builder.add_edge("block", END)

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Export used by langgraph.json / LangGraph CLI, alongside the existing `graph`.
study_graph = build_study_graph()
