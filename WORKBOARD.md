# WORKBOARD.md

Rule: maximum **3 items in NOW**. Everything else stays in NEXT, LATER or BLOCKED.

## NOW
1. Define and sell the first simple cash-generating offer(s) around Business Systems / Odoo / AI / ASPAR Solutions (pricing now corrected to 90 TND/mois — ADR 0005).
2. Record and publish the first founder-led master video, then repurpose it instead of building separate content factories.
3. Wire local Claude Code/MCP and downstream execution surfaces to the canonical gate in `agent-os/langgraph/` — pending live Odoo test once billing issue is resolved.

## NEXT
- Audit and clean up arbitrary Odoo records created in a previous session before any new data entry.
- Resolve Odoo billing issue (HTTP 303 since 2026-09-13), then build the `x_etude_business` Studio model and run one verified `odoo_sync` test.
- Validate pricing, delivery scope and contribution margin for the first sellable offer.
- Build one complete proof/demo around a real or representative business workflow.
- Simplify content production into one-source-to-many-outputs.
- Correct every published "30 TND/mois" reference (website, one-pagers) to 90 TND for new clients.
- Formalize the minimum client-facing ASPAR Agent scope versus internal delivery engine.
- Add concrete Drive/Canva/Odoo/Supabase source adapters only where an execution workflow requires them.

## LATER
- Mature proprietary ASPAR Business concepts after commercial traction and/or operating proof.
- Deeper cloud/local agent orchestration and scheduled multi-agent execution.
- Additional Supabase runtime components only when a concrete product need appears.
- More advanced content automation after repeated human-approved production reveals stable patterns.

## BLOCKED
- Full Brand Factory commercialization: blocked by lack of sufficient real operating proof and limited capital/time.
- `odoo_sync` live test: blocked by Odoo billing/HTTP 303 issue.
- Any promise of fully autonomous client operations: blocked until capability, permissions and reliability are demonstrated.

## Completed infrastructure
- Canonical shared repository established at `AsparGroup/aspar-group`.
- Shared active execution area established at `agent-os/`.
- Executable LangGraph + LangChain pre-execution gate migrated and CI-verified.
- `study_graph` — 7-phase feasibility gate with human interrupt at Phase 7 (CEO gate); CI-verified.
- `business_model_graph` — ASPAR's own line economics (Solutions, Cabinet, Building) with hard no-guessing rule on missing data.
- `blender_render_tool` — governance gate enforced: no render without `zonage_statut=Validé` and reference files.
- `generate_3d_visualization` node — Building→Blender after Phase 2.
- `odoo_sync` module written (pure function, testable offline); live Odoo test pending.
- `second_agent_worker` (Gemini, Google AI Studio) — CEO-confirmed 2026-09-14; draft/research only.
- `resilient_executor` (DeepSeek fallback) — continuity when primary LLM fails.
- `.gitignore` for `agent-os/langgraph/` — `.env` excluded.
- ADR 0004 revised: Notion formula/rollup banned for decisions; Odoo formulas allowed when verified readable.
- ADR 0005: ASPAR Solutions pricing corrected 30 → 90 TND/mois for new clients.
- Existing Claude agents preserved in `.claude/agents/`.
- Legacy NOTORIA V1 preserved under `archive/notoria-v1/` and marked non-active.
- Canonical root context, domain files, ADRs and Majdi SOURCE LOCK migrated.
- Target-repository CI verified: `8 passed in 0.39s`; smoke `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`.

## Gate rule
The required gate path is:
`intake -> classify -> resolve_role -> resolve_brand -> source_router -> retrieve_context -> validate -> SOURCE_LOCK PASS/STOP -> plan -> execute(preflight) -> QA -> writeback`.

Visual Majdi requests STOP when canonical Canva/Drive sources are not resolved; factual claims STOP without verified evidence.

## Execution rule
Before adding a new NOW task, move or finish an existing NOW item. Do not use this file as an unlimited backlog.
