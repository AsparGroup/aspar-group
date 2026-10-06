# HANDOFF.md

Use this file only for concise continuation context between substantial sessions or agents. Replace the active handoff when a newer one supersedes it; durable strategy belongs elsewhere.

## ACTIVE HANDOFF

**Date:** 2026-10-06
**From:** Claude Code
**To:** Claude Code / next ASPAR agent

### Objective
`AsparGroup/aspar-group` is the canonical shared repository. `agent-os/langgraph/` is the active gate. Wire Claude Code/MCP and downstream execution to this gate; test `odoo_sync` against a live Odoo instance once the billing issue is resolved.

### Read first
1. `STATE_ROUTER.md` → read `ETAT_LIVE_ASPAR.md` on Drive before any operational work
2. `ASPAR_CONTEXT.md`
3. `CURRENT_STATE.md` (updated 2026-10-06 — audit snapshot)
4. `WORKBOARD.md`
5. `agent-os/README.md`
6. Relevant brand `SOURCE_LOCK.md` for any visual/content task

### What was audited (2026-10-06)
Full audit of work done after the 2026-09-12 snapshot:
- Study pipeline (7-phase gate), business model pipeline, Blender governance gate, `odoo_sync`, `second_agent_worker` (Gemini), `resilient_executor` (DeepSeek fallback) all added and CI-verified.
- ADR 0004 revised (Notion formula/rollup banned; Odoo formulas allowed when verified readable).
- ADR 0005 (ASPAR Solutions pricing: 30 → 90 TND/mois for new clients, effective 2026-09-14).
- CURRENT_STATE.md, WORKBOARD.md and this HANDOFF updated accordingly.

### Known issues requiring CEO action
1. **Odoo billing / HTTP 303:** Odoo was unreachable as of 2026-09-13. Resolve billing before any Odoo integration test.
2. **Arbitrary Odoo records:** A previous session created records in Odoo without a validated task. Audit what was created before adding anything new.
3. **Pricing references:** Every published "30 TND/mois" reference for ASPAR Solutions is outdated (must become 90 TND for new clients).
4. **`odoo_sync` not live-tested:** The `odoo_sync` module is written as a pure function but has never run against a real Odoo instance. It requires the `x_etude_business` Studio model to exist with exact field names before it will work.

### Decisions confirmed
- Canonical repository: `AsparGroup/aspar-group`.
- Active runtime: `agent-os/langgraph/`.
- Second agent: Gemini (Google AI Studio), CEO-confirmed 2026-09-14.
- Claude agents: `.claude/agents/`, same root context.
- Legacy NOTORIA: `archive/notoria-v1/`, non-active.
- SOURCE LOCK remains mandatory; STOP bypasses plan/execute.
- `execute` remains preflight-only; actual external side effects stay downstream.
- Odoo is a system of record — never add arbitrary data without a scoped CEO-validated request.

### Next exact actions
1. Resolve Odoo billing (HTTP 303) — CEO action.
2. Build `x_etude_business` Studio model in Odoo with the field list in `odoo_sync.py`.
3. Run one `odoo_sync` test with a real study result.
4. Audit and clean up arbitrary Odoo records from the previous session.
5. Correct all published "30 TND/mois" ASPAR Solutions references.
6. Complete local Claude Code/MCP wiring to `agent-os/langgraph/` entry point.

## HANDOFF TEMPLATE

```markdown
**Date:** YYYY-MM-DD
**From:** agent/session
**To:** agent/session

### Objective

### What changed

### Decisions made

### Files changed

### Blockers

### Next exact action
```
