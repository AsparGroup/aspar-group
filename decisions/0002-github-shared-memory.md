# ADR 0002 — GitHub Markdown as shared ASPAR memory

**Status:** ACTIVE  
**Date:** 2026-09-11

## Context
ASPAR context has been spread across ChatGPT conversations, Claude Code/local Markdown files, Notion, Drive, Supabase and the founder's own memory. This forces repeated re-explanation, allows old assumptions to reappear and makes agent handoff unreliable.

Claude Code has strong local file awareness, while ChatGPT can access the connected GitHub repository. A neutral durable memory is therefore needed so neither AI is the sole owner of ASPAR context.

## Decision
Use versioned Markdown in GitHub as the shared durable memory for:
- stable ASPAR context;
- current strategic state;
- execution priorities;
- architecture decisions;
- concise inter-agent handoffs.

Minimum shared files:
- `CLAUDE.md`
- `ASPAR_CONTEXT.md`
- `CURRENT_STATE.md`
- `WORKBOARD.md`
- `HANDOFF.md`
- focused files under `domains/`
- ADRs under `decisions/`

GitHub Markdown is not an operational database. Live business execution remains in the appropriate operational system, primarily Odoo where relevant.

## Consequences
- ChatGPT and Claude Code can read the same durable context.
- Chats become reasoning surfaces rather than canonical memory.
- Important decisions become versioned and reviewable.
- The memory stays portable even if the AI tools change.
- The system remains intentionally small; uncontrolled growth into hundreds of Markdown files is discouraged.

## Supersedes
Any prior assumption that one chat history, one local Claude session, Notion or Supabase alone should serve as the complete ASPAR memory.
