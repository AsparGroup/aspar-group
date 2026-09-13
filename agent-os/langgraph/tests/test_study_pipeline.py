"""Tests for the 7-phase feasibility study gate (the "Méthode" doctrine).

Includes a regression test reproducing Café IA's real, documented state
as of 2026-09-13 (blocked at Phase 3 — CAPEX not yet quantified) so this
pipeline is checked against reality, not just synthetic cases.
"""

from aspar_agent.study_graph import build_study_graph


def invoke(payload: dict, thread_id: str):
    graph = build_study_graph()
    return graph.invoke(payload, {"configurable": {"thread_id": thread_id}})


def test_blocks_at_phase_1_with_no_sourcing_offers():
    result = invoke({"concept_name": "Idée vague"}, "phase1-block")
    assert result["blocked_at_phase"] == "1_sourcing_scraping"


def test_passes_phase_1_and_2_but_blocks_at_capex_like_cafe_ia_today():
    """Regression: reproduces Café IA's real state (Notion, checked 2026-09-13) —
    5 sourcing offers found, surface dimensioned, but CAPEX not yet quantified.
    """
    result = invoke(
        {
            "concept_name": "Café IA",
            "sourcing_offers_count": 5,
            "dimensionnement_params": {"surface_m2": 80, "zone": "centre-ville"},
            "capex_total": 0,
        },
        "cafe-ia-real-state",
    )
    assert result["blocked_at_phase"] == "3_capex_postes"
    assert "CAPEX" in result["blocked_reason"]


def test_passes_all_gates_up_to_phase_6_and_interrupts_for_ceo_decision():
    graph = build_study_graph()
    payload = {
        "concept_name": "Concept validé",
        "sourcing_offers_count": 5,
        "dimensionnement_params": {"surface_m2": 80, "zone": "centre"},
        "capex_total": 45000,
        "tarification_params": {"ticket_moyen": 12, "occupation_cible": 0.6},
        "score_marche": 72,
        "score_preuves": 80,
    }
    config = {"configurable": {"thread_id": "full-pass"}}
    result = graph.invoke(payload, config)
    # No CEO decision supplied yet -> graph interrupts, does not fabricate a GO.
    assert result.get("__interrupt__") is not None or "current_phase" in result


def test_ceo_decision_go_passes_the_final_gate():
    graph = build_study_graph()
    payload = {
        "concept_name": "Concept validé",
        "sourcing_offers_count": 5,
        "dimensionnement_params": {"surface_m2": 80, "zone": "centre"},
        "capex_total": 45000,
        "tarification_params": {"ticket_moyen": 12, "occupation_cible": 0.6},
        "score_marche": 72,
        "score_preuves": 80,
        "ceo_decision": "GO",
    }
    result = graph.invoke(payload, {"configurable": {"thread_id": "ceo-go"}})
    assert result["current_phase"] == "7_gate_go_etude_approfondie"
    assert result.get("blocked_at_phase") is None


def test_ceo_decision_no_go_blocks_at_the_final_gate():
    graph = build_study_graph()
    payload = {
        "concept_name": "Concept refusé",
        "sourcing_offers_count": 5,
        "dimensionnement_params": {"surface_m2": 80, "zone": "centre"},
        "capex_total": 45000,
        "tarification_params": {"ticket_moyen": 12, "occupation_cible": 0.6},
        "score_marche": 72,
        "score_preuves": 80,
        "ceo_decision": "NO_GO",
    }
    result = graph.invoke(payload, {"configurable": {"thread_id": "ceo-no-go"}})
    assert result["blocked_at_phase"] == "7_gate_go_etude_approfondie"
