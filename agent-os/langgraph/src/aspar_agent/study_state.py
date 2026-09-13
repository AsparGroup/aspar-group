"""State for the ASPAR business-concept feasibility study pipeline.

Codifies the 7-phase "Méthode" doctrine (previously tracked manually in
Notion) as a LangGraph state: Sourcing -> Dimensionnement -> CAPEX ->
Tarification -> Score marché -> Preuves -> Gate CEO. Each phase writes its
own signal and stops; the next phase is triggered only by its own gate
(no phase calls the next one directly) — same rule as the doctrine.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class PhaseResult(TypedDict, total=False):
    phase: str
    status: str  # "PASS" | "STOP"
    value: float | int | None
    threshold: str
    reason: str


class StudyState(TypedDict, total=False):
    concept_name: str
    concept_brief: str

    # Phase 1 — Sourcing scraping (seuil: >= 3 offres)
    sourcing_offers_count: int

    # Phase 2 — Dimensionnement surface (seuil: 2 paramètres saisis)
    dimensionnement_params: dict[str, Any]

    # Visualisation 3D (Building->Blender) — livrable déclenché après la Phase 2,
    # jamais bloquant pour la suite de l'étude (voir StudyNodeFactory.generate_3d_visualization)
    blender_work_dir: str
    render_status: str  # "PASS" | "STOP" | "" (pas encore tenté)
    render_path: str
    render_reason: str

    # Phase 3 — CAPEX postes (seuil: CAPEX total > 0 TND)
    capex_postes: dict[str, float]
    capex_total: float

    # Phase 4 — Tarification / occupation / CA (seuil: 2 paramètres saisis)
    tarification_params: dict[str, Any]

    # Phase 5 — Score marché (seuil: >= 60/100)
    score_marche: float

    # Phase 6 — Approfondir preuves (seuil: >= 75/100)
    score_preuves: float

    # Phase 7 — Gate GO étude approfondie (décision humaine CEO)
    ceo_decision: str  # "GO" | "NO_GO" | "" (pending)

    current_phase: str
    phase_results: list[PhaseResult]
    blocked_at_phase: str
    blocked_reason: str
    trace: list[str]
