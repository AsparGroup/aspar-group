# LangGraph + LangChain Pre-Execution Gate — Design

Date: 2026-09-12
Status: APPROVED FOR IMPLEMENTATION

## Goal

Build the executable pre-execution gate that every ASPAR Agent OS run must pass before any side-effecting execution such as image/carousel generation.

## Required flow

```text
REQUEST
→ INTAKE
→ CLASSIFY
→ RESOLVE_ROLE
→ RESOLVE_BRAND / DOMAIN
→ SOURCE_ROUTER
→ RETRIEVE_CONTEXT
→ VALIDATE
→ SOURCE_LOCK PASS / STOP
→ PLAN
→ EXECUTE
→ QA
→ WRITEBACK
```

A STOP result must bypass PLAN/EXECUTE and go directly to WRITEBACK/END.

## Run contract

Each run carries a structured state with:

- request
- role
- task
- domain
- brand
- context
- decision_criteria
- stop_conditions
- output_contract
- required_sources
- resolved_sources
- missing_sources
- conflicts
- source_lock_status: `PASS | STOP`
- stop_reason
- plan
- result
- qa_status
- qa_issues
- writeback
- trace

The system must not request or expose hidden chain-of-thought. `decision_criteria`, `assumptions` and a concise rationale are the auditable reasoning surface.

## LangGraph responsibility

LangGraph owns deterministic orchestration, state transitions, conditional routing, persistence hooks and the PASS/STOP gate.

The graph must compile before use and must support an in-memory checkpointer for tests/local smoke runs. Production persistence is supported through `PostgresSaver` using an injected PostgreSQL connection string.

## LangChain responsibility

LangChain is used for typed tools that perform reusable deterministic decisions inside the graph. The first implementation includes tools for brand resolution and SOURCE_LOCK evaluation. These tools are callable independently and are invoked by graph nodes.

No external LLM is required for the gate itself. This keeps the safety-critical preflight deterministic and testable.

## Source routing

Canonical ownership remains:

- GitHub Markdown: durable strategy, architecture, rules and SOURCE_LOCK files.
- Drive: evidence, source documents and approved heavy assets.
- Canva: canonical design production and Brand Kits.
- Odoo: business operational data.
- Supabase: optional runtime/backend state where a concrete workflow owns it.

The first executable resolver reads local GitHub/repository files directly and accepts externally resolved source records from MCP/connectors as run input. It does not duplicate Drive/Canva/Odoo data into GitHub.

## Majdi personal-brand rule

For `majdi_personal_brand`, `brands/majdi-personal-brand/SOURCE_LOCK.md` is always required.

Visual-generation requests also require externally resolved evidence for:

- Majdi Canva Brand Kit
- approved Drive visual/asset source

If either is unresolved, SOURCE_LOCK returns STOP. Text-only profile/copy tasks can pass with the local SOURCE_LOCK when no external visual asset is needed.

## Data/claim rule

If a request requires a factual statistic, KPI or case-study claim, the run must include verified source evidence. Missing evidence produces STOP rather than invented data.

## Execution boundary

The graph's first production milestone is a gate, not an autonomous content factory. The EXECUTE node returns an execution-ready contract/dry-run result; side-effecting Canva/image/social actions are connected only after the gate is proven.

## Persistence

- Test/local default: `InMemorySaver`.
- Production option: `PostgresSaver` from `langgraph-checkpoint-postgres`.
- Every persisted invocation requires a `thread_id` shorter than 255 characters.
- PostgreSQL setup is explicit and never stores secrets in Git.

## LangGraph application config

The repository must expose `langgraph.json` pointing to the compiled graph and install dependencies from the project root.

## Tests

Required automated tests:

1. LangChain tools are real tools and resolve Majdi correctly.
2. A text-only Majdi task reaches SOURCE_LOCK PASS.
3. A visual Majdi task without external canonical assets reaches STOP and never executes.
4. The same visual task passes when canonical external source records are supplied.
5. A claim/stat request without evidence stops.
6. A PASS run reaches QA and WRITEBACK.
7. Smoke script exercises both PASS and STOP paths.

## Success criteria

Configuration is considered closed only when:

- the graph imports and compiles;
- LangChain tools are invoked by graph nodes;
- tests pass;
- smoke test passes for PASS and STOP paths;
- `langgraph.json` points to the runnable graph;
- Postgres checkpointer integration imports successfully;
- no image generation occurs during implementation or verification.
