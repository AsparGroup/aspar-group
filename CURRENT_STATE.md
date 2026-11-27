# CURRENT_STATE.md

Snapshot: 2026-11-27

The live operational state is **not** in this file. It lives in `ETAT_LIVE_ASPAR.md` (see `STATE_ROUTER.md`) and must not be duplicated here. At this snapshot its header read `REVISION: 2`, last update 2026-10-06 by CODEX, no active lock. This repository is public: never copy client names, tasks or operational details from that file here.

## Business priority
ASPAR is in **monetization-before-expansion** mode.

Primary objective: generate sellable work and recurring cash flow before adding broad R&D or new infrastructure.

Near-term personal income target discussed: **5,000 TND/month**. This is a commercial target, not a guaranteed outcome.

## Current commercial direction
- **Majdi personal branding:** high priority as an acquisition/authority channel.
- **ASPAR Solutions:** high commercial priority; sell concrete Odoo/POS/business-system outcomes rather than technical stack details. New clients are priced at 90 TND/month per point of sale ([ADR 0005](decisions/0005-solutions-pricing-correction.md)).
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
- `AsparGroup/aspar-group` is the canonical shared repository between Claude Code, ChatGPT, Codex and future agents.
- Active orchestration lives under `agent-os/`.
- Claude Code remains the primary local builder/executor where local files, code and MCP access are required.
- ChatGPT is used for strategy, research, architecture, red-team and QA where appropriate.
- Handoffs between agents happen through repository state and structured files, not by manually retelling long chat histories.

## Core stack status
- **GitHub:** durable context, architecture, decisions, versioning.
- **LangGraph + LangChain:** deterministic orchestration under `agent-os/langgraph/` (see below).
- **Odoo:** operational center. Odoo Cloud (subscribed account) is the single Odoo target; local Odoo Community was abandoned and no local service, port `8069` or `docker compose` belongs in the normal flow (decision recorded in `ETAT_LIVE_ASPAR.md`, 2026-10-06).
- **Drive:** evidence, source documents, archives, heavy assets, and the master state file.
- **Canva:** design production.
- **Blender:** 3D production.
- **Claude Code/local stack:** local execution and code/files/MCP work.
- **Supabase:** backend actually used for the editorial cycle and described as control plane in `ETAT_LIVE_ASPAR.md`; still not mandatory for other workflows.
- **Notion:** outside core ([ADR 0001](decisions/0001-notion-out-of-core.md)) and set aside for now by the CEO (2026-11-27); legacy/reference only.

## Agent OS — what `agent-os/langgraph/` contains (checked in code, 2026-11-27)
- **Pre-execution gate** (`graph.py`, `nodes.py`): SOURCE_LOCK PASS/STOP; the `execute` node stays preflight-only.
- **Executor** (`executor.py`, `resilient_executor.py`, `second_agent_worker.py`): real execution after the gate passes, OpenAI by default (`gpt-4.1`); if the primary call fails, a second worker (Gemini free tier through its OpenAI-compatible endpoint) takes over and tags its result `verification_required: True`. Keys come from the environment (`OPENAI_API_KEY`, `GEMINI_API_KEY`); `agent-os/langgraph/.gitignore` excludes `.env`.
- **Feasibility study pipeline** (`study_*.py`): the 7-phase "Méthode" gate chain. A STOP routes to `block`; phase 7 is the CEO gate, a real human interrupt that never assumes `ceo_decision`.
- **Building→Blender node** (`blender_tools.py`): runs between the dimensioning and CAPEX phases, writes a bpy script and runs `blender --background --python`. It is a deliverable, not a gate: it never blocks the study, and it refuses to render unless `zonage_statut == "Validé"` and `fichiers_reference` is non-empty.
- **Odoo sync** (`odoo_sync.py`): writes computed study results into plain Odoo Studio fields (suggested model `x_etude_business`), the only place verdicts are displayed ([ADR 0004](decisions/0004-notion-no-formulas.md)). It calls `pipeline_cli`, which is not in this repository. Whether the Studio model exists in Odoo Cloud is not verified.
- **Business-model pipeline** (`business_model_*.py`): models ASPAR's own lines (Solutions, Cabinet, Building) and produces a diagnostic report for the CEO; it gates nothing.
- **Client web app** (`agent-os/client-agent/`, separate from the gate): the client-facing ASPAR AGENT on Cloudflare (Worker, Access, Workers AI, KV). 20 tests and a browser check pass; not deployed. See its README.

## Verification
2026-11-27, cloud session, Python 3.13, fresh virtual environment from `pyproject.toml` runtime dependencies plus pytest: `42 passed`; smoke `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}`.

Not re-verified in this snapshot: the GitHub Actions run on Python 3.12, `langgraph dev`, the optional PostgreSQL checkpointer.

## Instances and surfaces — declared by the CEO on 2026-11-27, public URLs checked the same day
None of these appear in `ETAT_LIVE_ASPAR.md` yet.
- **COO:** the CEO's own DSH instance (desktop app "ASPAR Group", Λ logo, project folder `asparincaspar`), internal use only. `ETAT_LIVE_ASPAR.md` also uses "mode COO" for CEO-delegated arbitration (2026-09-14); the link between the two usages is not established.
- **ASPAR AGENT (clients):** meant as the clients' dedicated instance. `agent.aspar.group` only answers with a Cloudflare redirect to `www.aspar.group/app/?assistant=1`, a static page with no assistant; nothing runs behind it. A Cloudflare-hosted replacement is ready in `agent-os/client-agent/` (built and tested, not deployed).
- **ERP client:** `client.aspar.group` (stated by the CEO), an Odoo login page titled « ASPAR OS ».
- **ASPAR OS:** the CEO's own internal tool according to the CEO. The Odoo behind `client.aspar.group` carries that name; whether they are the same instance is to be confirmed.
- `www.aspar.group`: online, served by Odoo behind Cloudflare; `aspar.group` redirects to it.

## Known memory conflicts
Rule: active ADRs of this repository prevail over older chat or document content.

1. **Notion: settled for now.** On 2026-11-27 the CEO said to set Notion aside for the moment, and [ADR 0001](decisions/0001-notion-out-of-core.md) (2026-09-11) stands. Agents do not read or write Notion, and create no Notion page or database, unless the CEO asks; existing Notion content is preserved, not deleted. Two older statements still make Notion central and live outside this repository, so their owner must update them: `ETAT_LIVE_ASPAR.md` §18 (2026-09-06: Notion as central memory, Drive abandoned, which also contradicts `STATE_ROUTER.md`), and the CEO's personal "Pilote technique" instructions (2026-08-15: Notion as ASPAR AGENT's brain, Promptage Blender queue in Notion). Until then both are obsolete. Blender renders run from the study pipeline under the zonage gate, not from a Notion queue.
2. **Mac copy vs this repository.** `ETAT_LIVE_ASPAR.md` (2026-10-06) describes a Mac working copy with 11 passing tests and a `widget_snapshot` graph command. Neither matches this repository (42 tests, no `widget_snapshot`), so the Mac copy has diverged from the canonical repository.

## Legacy NOTORIA
The former NOTORIA V1 orchestrator/media-worker monorepo is preserved under `archive/notoria-v1/` for reference. It is not active ASPAR runtime; TTS/video/lipsync workers must not be enabled by default.

## Constraints
- Avoid new paid tools unless they replace an existing cost/function or unlock a direct sale/delivery requirement.
- Avoid duplicate databases and duplicate task systems.
- Do not treat old chat content as current truth when it conflicts with active repository decisions.
- Do not publish unvalidated pricing or claim unproven proprietary concepts are established franchises.
- Side-effecting visual/content execution must continue to respect the SOURCE_LOCK contract and must not bypass missing canonical sources.

## Current architectural gap
The remaining integration work is local/runtime wiring: make Claude Code/MCP and downstream execution surfaces call `agent-os/langgraph/` as their mandatory entry point, after reconciling the diverged Mac working copy with this repository, then add concrete source adapters only when a real workflow requires them.
