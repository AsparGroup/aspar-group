# ASPAR Agent OS Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the verified ASPAR LangGraph/LangChain gate and the useful NOTORIA orchestration work into `ASPAR-SOLUTIONS/aspar-group` so Claude and ChatGPT use one repository and one shared execution area.

**Architecture:** `aspar-group` is the canonical repository. Active orchestration lives in `agent-os/`; the verified LangGraph pre-execution gate lives in `agent-os/langgraph/`; the older NOTORIA V1 monorepo is preserved under `archive/notoria-v1/` and is not active runtime. Shared ASPAR context and SOURCE LOCK files live at repository root so Claude and ChatGPT read the same durable context.

**Tech Stack:** Python 3.12, LangGraph, LangChain, pytest, PostgreSQL checkpointer, GitHub Actions, Claude Code agent files.

**Spec:** `agent-os/README.md`

## Global Constraints

- Canonical repository: `ASPAR-SOLUTIONS/aspar-group`.
- Shared runtime location: `agent-os/`.
- Do not activate legacy NOTORIA video/TTS/lipsync workers in the ASPAR runtime.
- Preserve source history by recording source repository/commit SHAs.
- SOURCE LOCK remains mandatory before visual execution.
- No image generation is part of this migration.

---

### Task 1: Establish shared repository structure

**Files:**
- Create: `agent-os/README.md`
- Create: `CLAUDE.md`
- Create/replace: root ASPAR context files

- [x] Add the common Agent OS contract and source provenance.
- [x] Put Claude and ChatGPT on the same repository-level context.
- [x] Verify paths and source commit references.

### Task 2: Migrate verified LangGraph gate

**Files:**
- Create: `agent-os/langgraph/pyproject.toml`
- Create: `agent-os/langgraph/langgraph.json`
- Create: `agent-os/langgraph/src/aspar_agent/*`
- Create: `agent-os/langgraph/tests/test_preexecution_gate.py`

- [x] Copy the verified gate into the canonical repository with relocation-only path adaptations.
- [x] Preserve PASS/STOP SOURCE LOCK routing.
- [x] Add CI in the target repository.

### Task 3: Preserve legacy NOTORIA V1 safely

**Files:**
- Create: `archive/notoria-v1/` from source tree commit `8486a7d577631fca6434fcac33217c870d629c9d`.

- [x] Preserve the old orchestrator/workers for reference.
- [x] Mark it legacy and non-active.

### Task 4: Unify Claude workspace

**Files:**
- Create: `.claude/agents/` from branch `claude/aspar-social-media-pipeline-756wh`.

- [x] Keep Claude agent definitions accessible in the same repository.
- [x] Make `CLAUDE.md` point to `agent-os/` and root context.

### Task 5: Verification

- [x] Open PR #4 from `consolidate/agent-os-notoria` to `main`.
- [x] Run GitHub Actions tests for `agent-os/langgraph`.
- [x] Confirm pytest and smoke test PASS before merge.
- [x] Record evidence before claiming completion.

## Verification evidence

Target-repository GitHub Actions run `34694733008`, job `103556151210`, completed successfully on Python 3.12:

- `8 passed in 0.39s`
- smoke: `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`
- package install succeeded with LangChain, LangGraph, LangGraph CLI/in-memory runtime, PostgreSQL checkpointer and psycopg extras.

The earlier RED run failed exactly because the canonical root Majdi SOURCE LOCK had not yet been migrated; adding that canonical source turned the relocation test suite green without weakening the gate.
