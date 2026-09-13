# ADR 0004 — Notion holds raw data only; no formulas or rollups compute decisions

**Status:** ACTIVE
**Date:** 2026-09-13

## Context
Elionor Sovereign's feasibility study (module Étude, base Évaluations) has never produced
a resolved GO/NO-GO verdict despite a well-normalized relational model (Zonage ↔ BOM CAPEX
↔ Promptage Blender, confirmed correctly designed in the Audit câblage relationnel du
15/08/2026). Investigation on 2026-09-13 found the actual cause: key aggregate fields
(Résultat net, Score investissabilité, CAPEX total hiérarchique, etc.) are Notion formula
or rollup properties. When read through the Notion MCP connector — the same access path
any agent or automation uses — these resolve to opaque references
(`formulaResult://...`, `rollupResult://...`) instead of plain numbers. The computation is
trapped inside Notion's formula engine: unreadable by any external tool, and in practice
never producing a usable verdict for CEO decision-making.

This is a general failure mode of the "relations + rollups as decision engine" pattern,
not specific to Elionor — the same pattern was about to be reused for Café IA's study
before this was caught.

## Decision
Notion properties must be plain data (text, number, select, status, date, file, person,
url) that a human or an agent enters directly. Notion formula and rollup property types
must not be used to compute scores, verdicts, sums, or any value a GO/NO-GO decision
depends on.

All such computation — sourcing counts, CAPEX totals, market/proof scores, GO/NO-GO
gates — is done in code (`agent-os/langgraph`, see `study_state.py` / `study_nodes.py` /
`study_graph.py`), which reads Notion's raw fields as plain inputs. The computed result
(score, verdict, GO/NO-GO) is never written back into Notion, not even as a read-only
display field — doing so would create a second copy of the same fact and violate SSOT
exactly as [ADR 0001](./0001-notion-out-of-core.md) already forbids for decisions and
runtime business records. The computed result lives in exactly one place: the pipeline's
own state/persistence (eventually the simple Odoo model already planned for this
pipeline). Anyone who needs to see the verdict reads it from there, not from Notion.

## Consequences
- Existing Notion formula/rollup fields used for scoring (Elionor's Évaluations base,
  P&L mensuel, etc.) are legacy — not deleted, but no longer trusted as the source of a
  verdict, and never repurposed to hold a copy of the code-computed result either. They
  should be phased out over time, not replaced field-for-field.
- Every new study/scoring workflow (Café IA and beyond) uses the coded 7-phase gate
  pipeline from day one instead of a new Notion relational scoring setup.
- Notion keeps its value as the human-facing data entry and browsing surface — this ADR
  does not remove Notion from the stack, it removes computation from Notion.
- Extends [ADR 0001](./0001-notion-out-of-core.md) (Notion out of core infrastructure):
  0001 keeps operational/decision records out of Notion; this ADR specifically forbids
  Notion's formula/rollup engine from being the place computation happens, even for data
  that does stay in Notion.

## Supersedes
Any implicit assumption that a sufficiently well-normalized Notion relational database
(even one following the "un propriétaire par relation" doctrine) is adequate as a scoring
or decision engine. Normalization solves data integrity; it does not solve computability
by tools outside Notion's own UI.
