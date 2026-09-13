"""Gate tool for the ASPAR feasibility study pipeline — one generalized
version of the threshold check used at every phase of the "Méthode"
doctrine, instead of one bespoke check per phase.
"""

from __future__ import annotations

from langchain.tools import tool


@tool("phase_gate")
def phase_gate_tool(
    phase: str,
    value: float,
    threshold: float,
    comparison: str = "gte",
    threshold_label: str = "",
) -> dict[str, object]:
    """Evaluate whether a study phase's measured value clears its threshold.

    `comparison` is one of "gte" (>=), "gt" (>), "eq" (==). Mirrors the
    doctrine's per-phase "seuil de passage" (e.g. CAPEX total > 0 TND,
    score marché >= 60/100).
    """
    if comparison == "gt":
        passed = value > threshold
    elif comparison == "eq":
        passed = value == threshold
    else:
        passed = value >= threshold

    label = threshold_label or f"{comparison} {threshold}"

    return {
        "phase": phase,
        "status": "PASS" if passed else "STOP",
        "value": value,
        "threshold": label,
        "reason": "" if passed else f"{phase}: valeur {value} n'atteint pas le seuil ({label})",
    }
