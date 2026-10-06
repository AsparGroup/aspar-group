# ASPAR Group — Canonical Repository

This repository is the shared source of truth for Claude, ChatGPT and the ASPAR Agent OS.

## Active structure

- `agent-os/` — active orchestration, LangGraph/LangChain gate, connectors, QA and runtime contracts.
- `.claude/agents/` — Claude-specific agent definitions kept in the same repository.
- `brands/`, `domains/`, `decisions/` — durable ASPAR context and SOURCE LOCK rules.
- `archive/notoria-v1/` — preserved historical NOTORIA V1 orchestrator and media-worker monorepo. It is legacy reference only and must not be treated as active ASPAR runtime.

## Operating rule

All new agentic work must start from this repository and resolve current context before execution. Visual/content execution must pass SOURCE LOCK before production.

## Migration provenance

- Verified LangGraph/LangChain gate source: `mynotoriastudio-cmd/Notoria-studio` commit `6124e45037950f4424eef5ce4f8a1f5cbd7f0e0f`.
- Legacy NOTORIA V1 source: `ASPAR-SOLUTIONS/aspar-group` commit `8486a7d577631fca6434fcac33217c870d629c9d`.
- Existing Claude agents source: branch `claude/aspar-social-media-pipeline-756wh`.

The old Airtable/Softr franchise-MVP description is obsolete and must not be used as current architecture.
