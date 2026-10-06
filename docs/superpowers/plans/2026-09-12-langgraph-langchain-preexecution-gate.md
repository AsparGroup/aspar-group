# LangGraph + LangChain Pre-Execution Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable, tested LangGraph + LangChain pre-execution gate with SOURCE_LOCK PASS/STOP behavior before any side-effecting ASPAR content generation.

**Architecture:** A deterministic `StateGraph` carries a typed run state through intake, routing, source resolution, validation, conditional SOURCE_LOCK, planning, dry execution, QA and writeback. LangChain `@tool` functions own reusable brand and source-lock decisions. External sources are injected as resolved records; local GitHub SOURCE_LOCK files are read directly. In-memory checkpointing is used for tests and a PostgresSaver context manager is provided for production wiring.

**Tech Stack:** Python 3.12, LangGraph, LangChain, langgraph-checkpoint-postgres, psycopg, pytest.

**Spec:** `docs/superpowers/specs/2026-09-12-langgraph-langchain-preexecution-gate-design.md`

## Global Constraints

- No image generation or carousel generation during this implementation.
- No hidden chain-of-thought storage or exposure.
- No secrets committed to Git.
- `brands/majdi-personal-brand/SOURCE_LOCK.md` is mandatory for Majdi personal-brand runs.
- Visual Majdi runs STOP when Canva Brand Kit or approved Drive asset source is unresolved.
- Claim/stat runs STOP without verified evidence.
- Side effects remain outside the first gate milestone; EXECUTE emits an execution-ready contract only.

---

### Task 1: Project package and RED tests

**Files:**
- Create: `pyproject.toml`
- Create: `tests/test_preexecution_gate.py`
- Create: `.github/workflows/langgraph-gate.yml`

**Interfaces:**
- Tests import `aspar_agent.graph.build_graph`, `aspar_agent.tools.resolve_brand_tool`, and `aspar_agent.persistence.postgres_checkpointer`.
- Production files intentionally do not exist at RED stage.

- [ ] **Step 1: Add Python package/dependency metadata** for Python 3.12, LangGraph, LangChain, pytest, and Postgres checkpointer support.
- [ ] **Step 2: Write tests** for Majdi text PASS, visual STOP, visual PASS with external sources, claim STOP, QA/writeback, and LangChain tool identity.
- [ ] **Step 3: Add CI workflow** running `python -m pytest -q` and `python -m aspar_agent.smoke`.
- [ ] **Step 4: Run CI and verify RED** because `aspar_agent` does not yet exist.

### Task 2: Minimal deterministic gate implementation

**Files:**
- Create: `src/aspar_agent/__init__.py`
- Create: `src/aspar_agent/state.py`
- Create: `src/aspar_agent/tools.py`
- Create: `src/aspar_agent/nodes.py`
- Create: `src/aspar_agent/graph.py`

**Interfaces:**
- `build_graph(checkpointer=None, repo_root=None) -> CompiledStateGraph`
- `resolve_brand_tool.invoke({"request": str}) -> dict`
- `source_lock_tool.invoke({...}) -> dict`

- [ ] **Step 1: Implement typed state.**
- [ ] **Step 2: Implement LangChain tools** for brand resolution and source-lock evaluation.
- [ ] **Step 3: Implement graph nodes** for every required stage.
- [ ] **Step 4: Implement conditional routing** so STOP bypasses PLAN/EXECUTE.
- [ ] **Step 5: Compile graph with InMemorySaver by default.**
- [ ] **Step 6: Re-run tests and fix only failures required by the spec.**

### Task 3: Persistence, LangGraph config and smoke runner

**Files:**
- Create: `src/aspar_agent/persistence.py`
- Create: `src/aspar_agent/smoke.py`
- Create: `langgraph.json`
- Modify: `.env.example`

**Interfaces:**
- `postgres_checkpointer(conn_string: str, setup: bool = False)` context manager yields `PostgresSaver`.
- `graph` exported from `src/aspar_agent/graph.py` for `langgraph.json`.

- [ ] **Step 1: Add lazy PostgresSaver integration** with explicit `setup()` option.
- [ ] **Step 2: Add smoke runner** covering one PASS and one STOP invocation with unique thread IDs.
- [ ] **Step 3: Add `langgraph.json`** with dependency root and graph export.
- [ ] **Step 4: Extend `.env.example`** with a blank PostgreSQL checkpoint URI and LangSmith key placeholder; commit no secrets.
- [ ] **Step 5: Run full tests and smoke command.**

### Task 4: Verification and durable status update

**Files:**
- Modify: `WORKBOARD.md`
- Modify: `CURRENT_STATE.md`
- Modify: `HANDOFF.md`

**Interfaces:**
- Status files must reflect evidence from CI/smoke, not assumptions.

- [ ] **Step 1: Verify CI/test output has zero failures.**
- [ ] **Step 2: Verify smoke output contains both `PASS` and `STOP` expected paths.**
- [ ] **Step 3: Update status docs only after verification.**
- [ ] **Step 4: Fast-forward `aspar-shared-memory` only after the verification gate is green.
