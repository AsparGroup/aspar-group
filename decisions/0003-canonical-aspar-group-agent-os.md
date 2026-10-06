# ADR 0003 — ASPAR Group as canonical repository and Agent OS location

**Status:** ACTIVE  
**Date:** 2026-09-12

## Context
Recent ASPAR work was split across `mynotoriastudio-cmd/Notoria-studio`, branches inside `AsparGroup/aspar-group`, GitHub Projects and Claude-specific agent files. This created multiple competing locations for shared memory and orchestration.

## Decision
`AsparGroup/aspar-group` is the canonical shared repository for Claude Code, ChatGPT and future ASPAR agents.

Within this repository:
- `agent-os/` is the active shared execution/orchestration area;
- `agent-os/langgraph/` contains the deterministic LangGraph/LangChain pre-execution gate;
- `.claude/agents/` contains Claude-specific agent definitions but must use the same root context and Agent OS;
- `archive/notoria-v1/` preserves the old NOTORIA V1 orchestrator/media-worker monorepo as legacy reference only;
- root Markdown files, `domains/`, `brands/` SOURCE LOCK files and `decisions/` are the durable shared memory.

No second canonical orchestration repository should be created without a later ADR superseding this one.

## Consequences
- Claude and ChatGPT share one durable repository and one runtime location.
- The old Notoria-studio repository becomes migration provenance, not the active source of truth.
- Legacy NOTORIA media workers are not activated by default in ASPAR Agent OS.
- Visual/content/Odoo side effects remain downstream of the SOURCE LOCK gate.
- GitHub Projects may track work, but code and durable architecture live in this repository.

## Migration provenance
- Verified gate source: `mynotoriastudio-cmd/Notoria-studio` commit `6124e45037950f4424eef5ce4f8a1f5cbd7f0e0f`.
- Legacy NOTORIA V1 source: `AsparGroup/aspar-group` commit `8486a7d577631fca6434fcac33217c870d629c9d`.
