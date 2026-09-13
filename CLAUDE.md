# CLAUDE.md — ASPAR shared repository router

This is the canonical repository shared by Claude Code, ChatGPT and future ASPAR agents.

## Mandatory reading order
Before substantial work:
0. Read `STATE_ROUTER.md`, then the real master file it points to (`ETAT_LIVE_ASPAR.md` on Drive). Never treat this repo alone as sufficient for live state.
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
- Claude-specific agent definitions: `.claude/agents/`.
- Historical NOTORIA V1 runtime: `archive/notoria-v1/` — legacy/reference only; do not activate its media workers by default.
- Do not create a second orchestration repository or duplicate Agent OS unless an explicit architecture decision supersedes this rule.

Required pre-execution flow:
`intake -> classify -> resolve_role -> resolve_brand -> source_router -> retrieve_context -> validate -> SOURCE_LOCK PASS/STOP -> plan -> execute(preflight) -> QA -> writeback`

No downstream Canva/image/social/Odoo side effect may bypass the SOURCE LOCK gate.

## Shared live-state concurrency rule
`ETAT_LIVE_ASPAR.md` is the single live operational state file. Claude Code, Codex, ChatGPT and workers may read it concurrently, but only one writer may modify it at a time.

Every writer MUST follow the protocol in `STATE_ROUTER.md`: reread latest state, acquire the shared lock, reread to confirm lock ownership, make only the minimal update, increment `REVISION`, verify after write, then release the lock. Never overwrite another writer's active lock, never write from stale content, and never create a parallel state file.

## Mandatory stack-first preflight
Before recommending, installing, or adding any new tool, SaaS, connector, database, automation platform, publishing platform, analytics product, or agent framework:
1. Resolve the current ASPAR stack from `CURRENT_STATE.md`, relevant domain files, and active decisions.
2. Check whether the requested capability is already covered by an existing tool or workflow.
3. Prefer the existing stack when it can satisfy the need with acceptable effort and reliability.
4. Add a new tool only if there is a verified capability gap, or if it clearly replaces an existing tool/cost or unlocks a direct sale/delivery need.
5. Do not recommend a paid or redundant service merely because a connector exists.
6. State the exact gap that justifies any new tool recommendation.

Current core stack to recognize before proposing additions:
- ChatGPT = strategy, research, architecture, QA and connected cloud tools.
- Claude Code/local stack = primary local builder/executor for local files, code and MCP work.
- LangGraph + LangChain = deterministic orchestration/pre-execution gate under `agent-os/langgraph/`.
- GitHub = durable context, code, architecture, decisions and versioning.
- Google Drive = source documents, evidence, approved assets and heavy files.
- Odoo = operational business system / CRM / sales / projects / stock / related operations.
- Canva = design production and editable social templates.
- Blender = 3D production when needed.
- Supabase = optional backend only for a concrete application/runtime need.
- Notion = legacy/reference/demo/client-use; not ASPAR core.

Cost rule: avoid new paid tools unless they replace an existing cost/function or unlock a direct sale/delivery requirement.

## Mandatory personal-brand preflight
For any task involving Majdi Garbouj personal branding, first read:
`brands/majdi-personal-brand/SOURCE_LOCK.md`

Do not ask the user to resend the visual identity if the canonical sources listed there are accessible and non-conflicting. External visual references may influence composition, hierarchy and rhythm only; they must never override the canonical Majdi palette, typography, signature, logo or approved assets.

## Source-of-truth rules
- GitHub Markdown = durable strategy, definitions, decisions, architecture and shared AI context.
- Odoo = business operations: CRM, projects, commercial activity, accounting/finance, sales, POS, stock and related operational records.
- Drive = heavy files, evidence, source documents and archives.
- Canva = design production.
- Blender = 3D production.
- Supabase = optional technical backend only when a concrete application/runtime need justifies it.
- Notion = legacy/reference/demo/client-use; not ASPAR core infrastructure.
- Chats = temporary reasoning surfaces, never canonical by themselves.

## Write-back protocol
After substantial work:
- update only the files whose durable truth changed;
- record important architecture/business decisions as a new ADR in `decisions/`;
- update `CURRENT_STATE.md` only for current state, not history;
- update `WORKBOARD.md` when execution priority changes;
- write a concise handoff in `HANDOFF.md` when another agent or session must continue.

## Safety and hygiene
Never commit passwords, API keys, tokens, private client credentials, identity documents or sensitive personal/client data.
Never invent missing ASPAR facts. Mark uncertainty explicitly.
Never silently delete an old decision: supersede it with a newer ADR.
