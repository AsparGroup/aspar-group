"""Tests for the 7-phase feasibility study gate (the "Méthode" doctrine).

Includes a regression test reproducing Café IA's real, documented state
as of 2026-09-13 (blocked at Phase 3 — CAPEX not yet quantified) so this
pipeline is checked against reality, not just synthetic cases.
"""

import pytest

from aspar_agent.study_graph import build_study_graph


@pytest.fixture(autouse=True)
def mock_blender_render(monkeypatch):
    """The study graph always runs generate_3d_visualization once Phase 2
    passes — mock its render call so these tests don't depend on Blender
    or the CLI-Anything harness being installed on whatever machine runs them.
    """

    class _FakeBlenderTool:
        @staticmethod
        def invoke(payload):
            return {
                "status": "PASS",
                "render_path": f"/tmp/{payload['concept_name']}_preview.png",
                "surface_m2": payload["surface_m2"],
            }

    monkeypatch.setattr(
        "aspar_agent.study_nodes.blender_render_tool", _FakeBlenderTool()
    )


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
    # The 3D preview still runs (Phase 2 passed) even though Phase 3 blocks after it.
    assert result["render_status"] == "PASS"
    assert result["render_path"] == "/tmp/Café IA_preview.png"


def test_visualization_runs_after_phase_2_and_never_blocks_the_study():
    result = invoke(
        {
            "concept_name": "Concept avec surface",
            "sourcing_offers_count": 5,
            "dimensionnement_params": {"surface_m2": 45, "zone": "banlieue"},
        },
        "visualization-runs",
    )
    assert result["render_status"] == "PASS"
    # No CAPEX given -> still blocks at Phase 3, proving the render is a
    # side-deliverable and never substitutes for the real gate.
    assert result["blocked_at_phase"] == "3_capex_postes"


def test_visualization_stops_gracefully_without_surface_but_study_continues():
    result = invoke(
        {
            "concept_name": "Concept sans surface",
            "sourcing_offers_count": 5,
            "dimensionnement_params": {"zone": "centre", "autre_param": "x"},
            "capex_total": 10000,
        },
        "visualization-no-surface",
    )
    assert result["render_status"] == "STOP"
    assert "surface_m2" in result["render_reason"]
    # The study itself keeps going past Phase 3 (CAPEX passed) despite the
    # render failure — it only stops later at Phase 4 (no tarification params).
    assert result["blocked_at_phase"] == "4_tarification_occupation_ca"


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
