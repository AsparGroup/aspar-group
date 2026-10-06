"""Writes the study pipeline's computed results into Odoo — the ONLY place
computed verdicts are displayed (never Notion, per ADR 0004: decisions/
0004-notion-no-formulas.md).

Odoo Online accepts no custom Python modules (confirmed in the "Écosystème
ASPAR" doctrine — Claude Code <-> Odoo runs through a hosted MCP connector,
not an installed addon). So the target Odoo model must be built with Odoo
Studio: plain fields only (char, float, selection, boolean), never a
computed/formula field. This module is what fills those plain fields — all
computation already happened in study_graph.py before this runs.

Model expected in Odoo (build via Studio, name suggested: x_etude_business):
  x_concept_name         (Char)
  x_current_phase        (Char)
  x_blocked_at_phase     (Char, empty if not blocked)
  x_blocked_reason       (Text, empty if not blocked)
  x_render_status        (Selection: PASS / STOP / pending)
  x_render_path          (Char)
  x_ceo_decision         (Selection: GO / NO_GO / pending)
  x_phase_results_json   (Text — raw JSON dump of phase_results, for audit;
                           display only, Studio must not parse/compute on it)

This module has NOT been tested against a live Odoo instance yet — Odoo was
unreachable (HTTP 303, billing-related) as of 2026-09-13. Verify field names
match the actual Studio model once it exists before relying on this.
"""

from __future__ import annotations

import json
from typing import Any


def study_result_to_odoo_record(state: dict[str, Any]) -> dict[str, Any]:
    """Flatten a StudyState result (from study_graph.invoke(...)) into the
    plain-field payload Odoo's x_etude_business model expects. Pure function,
    no Odoo call — makes it testable without a live Odoo connection.
    """
    return {
        "x_concept_name": state.get("concept_name", ""),
        "x_current_phase": state.get("current_phase", ""),
        "x_blocked_at_phase": state.get("blocked_at_phase") or "",
        "x_blocked_reason": state.get("blocked_reason") or "",
        "x_render_status": state.get("render_status") or "pending",
        "x_render_path": state.get("render_path") or "",
        "x_ceo_decision": state.get("ceo_decision") or "pending",
        "x_phase_results_json": json.dumps(state.get("phase_results", []), ensure_ascii=False),
    }


def sync_study_result_to_odoo(state: dict[str, Any], odoo_connection, record_id: int | None = None) -> int:
    """Write a study result to Odoo via the existing pipeline_cli connection
    (see aspar-site-editing skill: `get_cloud_connection()`). Creates a new
    x_etude_business record, or updates one if record_id is given (re-running
    the same concept through the pipeline should update its own record, not
    create a duplicate — one concept = one Odoo record, never two).

    `odoo_connection` is whatever get_cloud_connection() returns — not
    imported here to avoid a hard dependency on pipeline_cli in this module's
    tests; pass it in from the caller.
    """
    payload = study_result_to_odoo_record(state)

    if record_id:
        odoo_connection.write("x_etude_business", [record_id], payload)
        return record_id

    return odoo_connection.create("x_etude_business", payload)
