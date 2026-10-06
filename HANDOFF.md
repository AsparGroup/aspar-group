# HANDOFF.md

Use this file only for concise continuation context between substantial sessions or agents. Replace the active handoff when a newer one supersedes it; durable strategy belongs elsewhere.

## ACTIVE HANDOFF

**Date:** 2026-09-12
**From:** ChatGPT
**To:** Claude Code / next ASPAR agent

### Objective
Use `AsparGroup/aspar-group` as the canonical shared repository. The active pre-execution runtime is `agent-os/langgraph/`; all local Claude Code/MCP and downstream Canva/image/social execution must pass through it before side effects.

### Read first
1. `ASPAR_CONTEXT.md`
2. `CURRENT_STATE.md`
3. `WORKBOARD.md`
4. `agent-os/README.md`
5. Relevant brand `SOURCE_LOCK.md`

### What changed
- Established the shared `agent-os/` location in ASPAR Group.
- Migrated the LangGraph/LangChain gate from `mynotoriastudio-cmd/Notoria-studio` source commit `6124e45037950f4424eef5ce4f8a1f5cbd7f0e0f`.
- Preserved the former NOTORIA V1 monorepo under `archive/notoria-v1/` as non-active legacy.
- Brought existing Claude agent definitions under `.claude/agents/` in the same repository.
- Migrated canonical ASPAR context, domain docs, ADRs and Majdi SOURCE LOCK into the repository root.
- Added target-repository CI for the migrated gate.

### Verification evidence
GitHub Actions run `34694733008`, job `103556151210`, succeeded on Python 3.12:
- `8 passed in 0.39s`
- smoke: `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`

A prior RED run failed specifically because the canonical root Majdi SOURCE LOCK was absent; migration of that source made the tests pass without relaxing validation.

### Decisions made
- Canonical repository: `AsparGroup/aspar-group`.
- Shared active runtime location: `agent-os/`.
- Active gate: `agent-os/langgraph/`.
- Claude agents: `.claude/agents/`, using the same root context/runtime.
- Legacy NOTORIA video/TTS/lipsync runtime must not be activated by default.
- SOURCE LOCK remains mandatory; STOP bypasses plan/execute.
- `execute` remains preflight-only; actual external side effects stay downstream.

### Remaining blocker
Local Mac/Claude Code/MCP caller wiring still requires local verification. The repository migration itself is CI-verified.

### Next exact action
1. Sync `AsparGroup/aspar-group` locally after PR #4 is merged.
2. From `agent-os/langgraph/`, install `.[dev,postgres]`, run pytest and smoke, then start `langgraph dev --no-browser`.
3. Point Claude Code/MCP and downstream executors at this gate.
4. Do not bypass SOURCE LOCK for visual or factual-claim tasks.

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
