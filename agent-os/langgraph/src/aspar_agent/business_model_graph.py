"""Graph for ASPAR's own business-line modeling (Solutions, Cabinet,
Building, future lines). Three nodes: compute derived values -> compute
score/audit trail -> done. No human-in-the-loop gate here (unlike
study_graph.py's Phase 7) — this pipeline produces a diagnostic report for
the CEO to read and decide on, it does not gate a GO/NO-GO by itself.
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .business_model_state import BusinessModelState
from .business_model_tools import (
    marge_brute_mensuelle,
    payback_mois,
    profit_net_mensuel,
    score_modele_economique,
    seuil_rentabilite_nb_clients,
)


def _compute_derived(state: BusinessModelState) -> dict[str, Any]:
    marge = marge_brute_mensuelle(state.get("ca_mensuel_tnd"), state.get("couts_variables_mensuels_tnd"))
    profit = profit_net_mensuel(marge, state.get("couts_fixes_mensuels_tnd"))
    payback = payback_mois(state.get("capex_ouverture_tnd"), profit)
    seuil = seuil_rentabilite_nb_clients(
        state.get("couts_fixes_mensuels_tnd"),
        state.get("prix_unitaire_tnd"),
        state.get("cout_variable_unitaire_tnd"),
    )
    return {
        "marge_brute_mensuelle_tnd": marge,
        "profit_net_mensuel_tnd": profit,
        "payback_mois": payback,
        "seuil_rentabilite_nb_clients": seuil,
        "trace": [*state.get("trace", []), "compute_derived"],
    }


def _compute_score(state: BusinessModelState) -> dict[str, Any]:
    score, manquants = score_modele_economique(state)
    return {
        "score_modele_economique": score,
        "donnee_manquante": manquants,
        "trace": [*state.get("trace", []), "compute_score"],
    }


def build_business_model_graph(checkpointer=None):
    builder = StateGraph(BusinessModelState)
    builder.add_node("compute_derived", _compute_derived)
    builder.add_node("compute_score", _compute_score)

    builder.add_edge(START, "compute_derived")
    builder.add_edge("compute_derived", "compute_score")
    builder.add_edge("compute_score", END)

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


business_model_graph = build_business_model_graph()
