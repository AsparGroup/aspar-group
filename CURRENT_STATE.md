# CURRENT_STATE.md

Snapshot: 2026-10-06

## Business priority
ASPAR is in **monetization-before-expansion** mode.

Primary objective: generate sellable work and recurring cash flow before adding broad R&D or new infrastructure.

Near-term personal income target discussed: **5,000 TND/month**. This is a commercial target, not a guaranteed outcome.

## Current commercial direction
- **Majdi personal branding:** high priority as an acquisition/authority channel.
- **ASPAR Solutions:** high commercial priority; sell concrete Odoo/POS/business-system outcomes. Pricing corrected to **90 TND/mois/point de vente** for new clients (ADR 0005). Existing clients at 30 TND are not retroactively migrated — that requires a separate count-first assessment.
- **ASPAR Business:** sell studies, project design/structuring and preparation/execution support.
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
- `AsparGroup/aspar-group` is the canonical shared repository between Claude Code, ChatGPT and future agents.
- Active orchestration lives under `agent-os/`.
- Claude Code remains the primary local builder/executor where local files, code and MCP access are required.
- ChatGPT is used for strategy, research, architecture, red-team and QA where appropriate.
- Handoffs between agents happen through repository state and structured files, not by manually retelling long chat histories.

## Core stack status
- **GitHub:** durable context, architecture, decisions, versioning.
- **LangGraph + LangChain:** consolidated under `agent-os/langgraph/`. CI-verified (8 passed, 0.39s). Includes:
  - Pre-execution SOURCE_LOCK gate
  - `study_graph` — 7-phase feasibility gate with human interrupt at Phase 7 (CEO gate)
  - `business_model_graph` — ASPAR's own line economics (Solutions, Cabinet, Building)
  - `generate_3d_visualization` — Building→Blender preview after Phase 2
  - `blender_render_tool` — governance gate: refuses render without `zonage_statut=Validé` and reference files
  - `odoo_sync` — writes computed study results to Odoo Studio plain fields (x_etude_business); **not yet tested against a live Odoo instance** — Odoo was HTTP 303/unreachable (billing issue) as of 2026-09-13; verify before relying on it
  - `executor` — primary LLM executor (OpenAI/ChatGPT), with DeepSeek resilient fallback (`resilient_executor`)
  - `second_agent_worker` — Gemini (Google AI Studio free tier), confirmed CEO decision 2026-09-14; output is DRAFT/RESEARCH only, never a decision-ready fact
- **Odoo:** intended operational center. **Status: unreachable (HTTP 303, billing issue) as of 2026-09-13** — resolve billing before testing `odoo_sync` or any live Odoo integration. Do not create arbitrary records in Odoo without an explicit validated task.
- **Drive:** evidence, source documents, archives and heavy assets. `ETAT_LIVE_ASPAR.md` lives here (Drive ID `1TBPbFeolSAyRBvE4WyqOnQiNh2oKdbqP`).
- **Canva:** design production.
- **Blender:** 3D production — governance gate active; render requires CEO-approved sources.
- **Claude Code/local stack:** local execution and code/files/MCP work.
- **Supabase:** optional technical backend; not mandatory for every workflow.
- **Notion:** outside core; retained only as legacy/reference/demo/client-use. Formula/rollup fields confirmed opaque through MCP connector (ADR 0004) — do not use for computed decisions.

## Canonical LangGraph verification
Target-repository GitHub Actions run `34694733008` verified the gate on Python 3.12:
- `8 passed in 0.39s`
- smoke: `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`

## Pricing status
- **ASPAR Solutions (new clients):** 90 TND/mois/point de vente (ADR 0005, effective 2026-09-14)
- **Existing clients at 30 TND:** not migrated; requires count-first assessment before any action
- Every published "30 TND" reference (website, one-pagers) is now wrong for new clients and must be corrected once the site is back online

## Odoo note — known data quality risk
A previous session created records in Odoo without an explicit validated task. Before relying on any Odoo data, audit the records present and confirm they correspond to real business operations. Do not add new records without a clear, scoped request from the CEO.

## Legacy NOTORIA
The former NOTORIA V1 orchestrator/media-worker monorepo is preserved under `archive/notoria-v1/` for reference. It is not active ASPAR runtime; TTS/video/lipsync workers must not be enabled by default.

## Constraints
- Avoid new paid tools unless they replace an existing cost/function or unlock a direct sale/delivery requirement.
- Avoid duplicate databases and duplicate task systems.
- Do not treat old chat content as current truth when it conflicts with active repository decisions.
- Do not publish unvalidated pricing or claim unproven proprietary concepts are established franchises.
- Side-effecting visual/content execution must continue to respect the SOURCE_LOCK contract and must not bypass missing canonical sources.
- **Never create arbitrary Odoo records without a validated, scoped request.** Odoo is an operational system of record, not a sandbox.

## Remaining integration gap
`odoo_sync` and the full local/MCP→`agent-os/langgraph` wiring are not yet end-to-end verified on a live Odoo instance. These require: (1) Odoo billing resolved, (2) Studio model `x_etude_business` built with the exact fields specified in `odoo_sync.py`, (3) a single test run with a real study result before any production use.
