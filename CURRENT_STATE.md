# CURRENT_STATE.md

Snapshot: 2026-09-12

## Business priority
ASPAR is in **monetization-before-expansion** mode.

Primary objective: generate sellable work and recurring cash flow before adding broad R&D or new infrastructure.

Near-term personal income target discussed: **5,000 TND/month**. This is a commercial target, not a guaranteed outcome.

## Current commercial direction
- **Majdi personal branding:** high priority as an acquisition/authority channel.
- **ASPAR Solutions:** high commercial priority; sell concrete Odoo/POS/business-system outcomes rather than technical stack details.
- **ASPAR Business:** sell studies, project design/structuring and preparation/execution support; do not depend on finishing the full Brand Factory.
- **ASPAR Building:** sell opportunistically where a real physical project exists.
- **ASPAR Franchise:** sell selectively when a network/duplication need exists.
- **Proprietary concepts / Brand Factory:** R&D/HOLD for broad commercialization until sufficient operating proof exists.

## Content direction
- One master idea or real case should feed multiple relevant channels.
- Majdi is the primary media/voice layer.
- ASPAR vertical pages are specialist proof/conversion surfaces, not five independent full-time media companies.
- Human recording and judgment remain important; AI should multiply, cut, reformat and assist rather than replace the founder's voice.
- Canva remains the design production environment; do not rebuild Canva capabilities elsewhere without a clear reason.

## Shared-memory direction
- `ASPAR-SOLUTIONS/aspar-group` is the canonical shared repository between Claude Code, ChatGPT and future agents.
- Active orchestration lives under `agent-os/`.
- Claude Code remains the primary local builder/executor where local files, code and MCP access are required.
- ChatGPT is used for strategy, research, architecture, red-team and QA where appropriate.
- Handoffs between agents happen through repository state and structured files, not by manually retelling long chat histories.

## Core stack status
- **GitHub:** durable context, architecture, decisions, versioning.
- **LangGraph + LangChain:** executable deterministic pre-execution gate is now consolidated under `agent-os/langgraph/`; SOURCE_LOCK PASS/STOP, conditional routing, LangChain tools, in-memory checkpointing, optional PostgresSaver, `langgraph.json`, CLI dependency and smoke runner are present.
- **Odoo:** intended operational center for CRM, projects, commercial operations, accounting/finance, sales, POS, stock and related business processes.
- **Drive:** evidence, source documents, archives and heavy assets.
- **Canva:** design production.
- **Blender:** 3D production.
- **Claude Code/local stack:** local execution and code/files/MCP work.
- **Supabase:** optional technical backend; not mandatory for every workflow.
- **Notion:** outside core; retained only as legacy/reference/demo/client-use where useful.

## Canonical LangGraph verification
Target-repository GitHub Actions run `34694733008` verified the migrated gate on Python 3.12:
- `8 passed in 0.39s`;
- smoke output: `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`;
- LangChain, LangGraph, LangGraph CLI/in-memory runtime and PostgreSQL checkpoint dependencies installed successfully.

The migration used a relocation-specific RED test first: before `brands/majdi-personal-brand/SOURCE_LOCK.md` was added to the canonical repository, the suite produced the expected STOP failures. Adding the canonical source made the same gate green without weakening the validation rules.

The EXECUTE node intentionally remains `preflight_only`: it returns an execution-ready contract and does not itself call Canva/image/social side effects.

## Legacy NOTORIA
The former NOTORIA V1 orchestrator/media-worker monorepo is preserved under `archive/notoria-v1/` for reference. It is not active ASPAR runtime; TTS/video/lipsync workers must not be enabled by default.

## Constraints
- Avoid new paid tools unless they replace an existing cost/function or unlock a direct sale/delivery requirement.
- Avoid duplicate databases and duplicate task systems.
- Do not treat old chat content as current truth when it conflicts with active repository decisions.
- Do not publish unvalidated pricing or claim unproven proprietary concepts are established franchises.
- Side-effecting visual/content execution must continue to respect the SOURCE_LOCK contract and must not bypass missing canonical sources.

## Current architectural gap
The canonical Agent OS repository migration is CI-verified. The remaining integration work is local/runtime wiring: make Claude Code/MCP and downstream execution surfaces call `agent-os/langgraph/` as their mandatory entry point, then add concrete source adapters only when a real workflow requires them.
