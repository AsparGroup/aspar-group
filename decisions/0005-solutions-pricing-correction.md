# ADR 0005 — ASPAR Solutions pricing corrected from 30 to 90 TND/mois (new clients)

**Status:** ACTIVE
**Date:** 2026-09-14

## Context
ASPAR Solutions was priced at 30 TND/mois/point de vente with no cost-plus
verification behind that number — it was a posted price, never checked
against real variable cost. On 2026-09-14 the CEO disclosed the real Odoo
backend cost: 13 USD/mois/client (≈40.3 TND at 3.1 TND/USD). Adding an
estimated support cost (0.5h/mois/client at the documented internal build
rate of 50 TND/h = 25 TND/mois) gives a real variable cost of **65.3
TND/mois/client**.

At 30 TND, ASPAR Solutions loses 35.3 TND/mois on every client, before
counting any development CAPEX amortization. This was never visible
before because no business-model computation existed for ASPAR Solutions
as its own line (see `business_model_graph.py`, added 2026-09-13) — the
price had never been checked against cost.

## Decision
New ASPAR Solutions clients are priced at **90 TND/mois/point de vente**
(cost-plus, 30% target margin over the 65.3 TND real variable cost),
effective 2026-09-14. This replaces the 30 TND price for new signups.

Existing clients already on 30 TND (count not yet confirmed) are **not**
migrated retroactively by this decision — an abrupt 3x price increase on
existing relationships risks trust/churn and needs its own count-first
assessment before any action. This ADR governs new clients only.

## Consequences
- Every existing published reference to "30 TND/mois" (website, one-pagers,
  Notion pricing page) is now wrong for new clients and must be corrected
  once the site is back online (currently blocked, unrelated Odoo billing
  issue).
- The 65.3 TND variable-cost figure includes an *estimated* support cost
  (0.5h/mois, a placeholder), not yet a measured real support hours figure
  — flagged in `business_model_state.py`'s `donnee_manquante` as an open
  item, not treated as fully verified.
- Development CAPEX for ASPAR Solutions is still unknown — this ADR fixes
  per-client unit economics (marginal profitability), not the payback
  period on the software's original development cost, which remains
  uncomputed until that CAPEX figure is provided.
- A parallel, non-blocking workstream should investigate whether the 40.3
  TND/mois backend cost can be reduced (e.g. cheaper Odoo hosting tier) —
  this ADR does not close that question, it only stops the immediate loss
  by fixing price now rather than waiting on a cost investigation.

## Supersedes
The unverified 30 TND/mois price point for new ASPAR Solutions clients.
