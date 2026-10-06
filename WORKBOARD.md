# WORKBOARD.md

Rule: maximum **3 items in NOW**. Everything else stays in NEXT, LATER or BLOCKED.

## NOW
1. Define and sell the first simple cash-generating offer(s) around Business Systems / Odoo / AI / ASPAR Solutions.
2. Record and publish the first founder-led master video, then repurpose it instead of building separate content factories.
3. Wire local Claude Code/MCP and downstream execution surfaces to the canonical gate in `agent-os/langgraph/`.

## NEXT
- Validate pricing, delivery scope and contribution margin for the first sellable offer.
- Build one complete proof/demo around a real or representative business workflow.
- Simplify content production into one-source-to-many-outputs.
- Formalize the minimum client-facing ASPAR Agent scope versus internal delivery engine.
- Add concrete Drive/Canva/Odoo/Supabase source adapters only where an execution workflow requires them; keep the current injected-source interface as the boundary.

## LATER
- Mature proprietary ASPAR Business concepts after commercial traction and/or operating proof.
- Deeper cloud/local agent orchestration and scheduled multi-agent execution.
- Additional Supabase runtime components only when a concrete product need appears.
- More advanced content automation after repeated human-approved production reveals stable patterns.

## BLOCKED
- Full Brand Factory commercialization: blocked by lack of sufficient real operating proof and limited capital/time.
- Any promise of fully autonomous client operations: blocked until capability, permissions and reliability are demonstrated.

## Completed infrastructure
- Canonical shared repository established at `AsparGroup/aspar-group`.
- Shared active execution area established at `agent-os/`.
- Executable LangGraph + LangChain pre-execution gate migrated to `agent-os/langgraph/`.
- Existing Claude agents preserved in `.claude/agents/` in the same repository.
- Legacy NOTORIA V1 preserved under `archive/notoria-v1/` and marked non-active.
- Canonical root context, domain files, ADRs and Majdi SOURCE LOCK migrated.
- Target-repository CI verified: `8 passed in 0.39s`; smoke `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`.

## Gate rule
The required gate path is:
`intake -> classify -> resolve_role -> resolve_brand -> source_router -> retrieve_context -> validate -> SOURCE_LOCK PASS/STOP -> plan -> execute(preflight) -> QA -> writeback`.

Visual Majdi requests STOP when canonical Canva/Drive sources are not resolved; factual claims STOP without verified evidence.

## Execution rule
Before adding a new NOW task, move or finish an existing NOW item. Do not use this file as an unlimited backlog.
