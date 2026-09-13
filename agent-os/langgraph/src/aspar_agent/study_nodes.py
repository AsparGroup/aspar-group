"""Nodes for the ASPAR feasibility study pipeline (the "Méthode" doctrine,
7 phases: Sourcing -> Dimensionnement -> CAPEX -> Tarification -> Score
marché -> Preuves -> Gate CEO). Each node writes its own signal and stops
— the graph's conditional edges decide whether the next phase runs, no
node calls the next one directly (same rule as the Notion doctrine it
codifies).
"""

from __future__ import annotations

from typing import Any

from .study_state import PhaseResult, StudyState
from .study_tools import phase_gate_tool


def _trace(state: StudyState, name: str) -> list[str]:
    return [*state.get("trace", []), name]


def _record(results: list[PhaseResult], result: dict[str, Any]) -> list[PhaseResult]:
    return [*results, result]  # type: ignore[list-item]


class StudyNodeFactory:
    """Build the 7 phase nodes of the feasibility study gate."""

    def phase_sourcing(self, state: StudyState) -> dict[str, Any]:
        offers = state.get("sourcing_offers_count", 0)
        gate = phase_gate_tool.invoke(
            {
                "phase": "1_sourcing_scraping",
                "value": offers,
                "threshold": 3,
                "comparison": "gte",
                "threshold_label": ">= 3 offres",
            }
        )
        return {
            "current_phase": "1_sourcing_scraping",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_sourcing"),
        }

    def phase_dimensionnement(self, state: StudyState) -> dict[str, Any]:
        params = state.get("dimensionnement_params", {})
        gate = phase_gate_tool.invoke(
            {
                "phase": "2_dimensionnement_surface",
                "value": len(params),
                "threshold": 2,
                "comparison": "gte",
                "threshold_label": "2 paramètres saisis",
            }
        )
        return {
            "current_phase": "2_dimensionnement_surface",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_dimensionnement"),
        }

    def phase_capex(self, state: StudyState) -> dict[str, Any]:
        capex_total = state.get("capex_total", 0.0)
        gate = phase_gate_tool.invoke(
            {
                "phase": "3_capex_postes",
                "value": capex_total,
                "threshold": 0,
                "comparison": "gt",
                "threshold_label": "CAPEX total > 0 TND",
            }
        )
        return {
            "current_phase": "3_capex_postes",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_capex"),
        }

    def phase_tarification(self, state: StudyState) -> dict[str, Any]:
        params = state.get("tarification_params", {})
        gate = phase_gate_tool.invoke(
            {
                "phase": "4_tarification_occupation_ca",
                "value": len(params),
                "threshold": 2,
                "comparison": "gte",
                "threshold_label": "2 paramètres saisis",
            }
        )
        return {
            "current_phase": "4_tarification_occupation_ca",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_tarification"),
        }

    def phase_score_marche(self, state: StudyState) -> dict[str, Any]:
        score = state.get("score_marche", 0.0)
        gate = phase_gate_tool.invoke(
            {
                "phase": "5_score_marche",
                "value": score,
                "threshold": 60,
                "comparison": "gte",
                "threshold_label": ">= 60/100",
            }
        )
        return {
            "current_phase": "5_score_marche",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_score_marche"),
        }

    def phase_preuves(self, state: StudyState) -> dict[str, Any]:
        score = state.get("score_preuves", 0.0)
        gate = phase_gate_tool.invoke(
            {
                "phase": "6_approfondir_preuves",
                "value": score,
                "threshold": 75,
                "comparison": "gte",
                "threshold_label": ">= 75/100",
            }
        )
        return {
            "current_phase": "6_approfondir_preuves",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_preuves"),
        }

    def phase_ceo_gate(self, state: StudyState) -> dict[str, Any]:
        """Phase 7 — human gate. The graph interrupts here; the caller
        resumes with `ceo_decision` set to "GO" or "NO_GO". This node
        never guesses the decision — it only records what was provided.
        """
        decision = state.get("ceo_decision", "")
        gate = {
            "phase": "7_gate_go_etude_approfondie",
            "status": "PASS" if decision == "GO" else "STOP",
            "value": decision,
            "threshold": "Décision humaine CEO (GO/NO_GO)",
            "reason": "" if decision == "GO" else "En attente ou refus de la décision CEO",
        }
        return {
            "current_phase": "7_gate_go_etude_approfondie",
            "phase_results": _record(state.get("phase_results", []), gate),
            "trace": _trace(state, "phase_ceo_gate"),
        }

    def block(self, state: StudyState) -> dict[str, Any]:
        last = state.get("phase_results", [])[-1] if state.get("phase_results") else {}
        return {
            "blocked_at_phase": last.get("phase", "unknown"),
            "blocked_reason": last.get("reason", ""),
            "trace": _trace(state, "block"),
        }
