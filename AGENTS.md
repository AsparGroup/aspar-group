# AGENTS.md — Codex router for the ASPAR shared repository

This is the canonical repository shared by Claude Code, ChatGPT and future ASPAR agents.

## Mandatory reading order
Before substantial work:
0. Read `STATE_ROUTER.md`, then the real master file it points to (`ETAT_LIVE_ASPAR.md` on Drive) — it holds the real operational state that nothing in this repo duplicates. Never treat this repo alone as sufficient for live state.
1. Read `ASPAR_CONTEXT.md`.
2. Read `CURRENT_STATE.md`.
3. Read `WORKBOARD.md`.
4. Read only the relevant `domains/*.md` file(s).
5. For automation/agent/runtime work, read `agent-os/README.md`.
6. Read ADRs in `decisions/` only when a decision or historical conflict matters.
7. For any brand/design/content task, resolve the relevant brand SOURCE LOCK before execution.

Do not load every file by default.

## Canonical Agent OS location
- Active orchestration: `agent-os/langgraph/`.
- Historical NOTORIA V1 runtime: `archive/notoria-v1/` — legacy/reference only; do not activate its media workers by default.

## Shared-state write rule
`ETAT_LIVE_ASPAR.md` is the single live operational state file. Multiple agents may read it concurrently, but only one writer may modify it at a time.

Before every write, follow `STATE_ROUTER.md` exactly: reread latest state, acquire the shared lock, reread to confirm lock ownership, apply the minimal change, increment `REVISION`, verify after write, then release the lock. Never overwrite an active lock, never write from stale content, never create a dated copy or parallel state file.
