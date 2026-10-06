# ASPAR Agent OS

`agent-os/` is the shared execution area for Claude Code, ChatGPT and future ASPAR agents inside the canonical repository `ASPAR-SOLUTIONS/aspar-group`.

## Active runtime

`agent-os/langgraph/` contains the verified LangGraph + LangChain pre-execution gate migrated from `mynotoriastudio-cmd/Notoria-studio` commit `6124e45037950f4424eef5ce4f8a1f5cbd7f0e0f`.

Required flow:

`intake -> classify -> resolve_role -> resolve_brand -> source_router -> retrieve_context -> validate -> SOURCE_LOCK PASS/STOP -> plan -> execute(preflight) -> QA -> writeback`

The `execute` node is intentionally preflight-only. Canva, image, publishing, Odoo and other side effects stay downstream and must not bypass SOURCE LOCK.

## Shared context

Before substantial work, agents read repository-root context in this order:
1. `ASPAR_CONTEXT.md`
2. `CURRENT_STATE.md`
3. `WORKBOARD.md`
4. relevant `domains/*.md`
5. relevant brand `SOURCE_LOCK.md`
6. ADRs in `decisions/` only when needed

Claude-specific definitions stay under `.claude/agents/`, but they share the same root context and Agent OS.

## Legacy NOTORIA

`archive/notoria-v1/` preserves the former NOTORIA V1 orchestrator/media-worker monorepo for reference. It is not active ASPAR runtime and its TTS/video/lipsync workers must not be enabled by default.

## Local verification

From `agent-os/langgraph/`:

```bash
python -m pip install -e ".[dev,postgres]"
python -m pytest -q
python -m aspar_agent.smoke
langgraph dev --no-browser
```

Expected smoke result:

```json
{"pass_path":"PASS","status":"ok","stop_path":"STOP"}
```

## Source provenance

- Active gate source commit: `6124e45037950f4424eef5ce4f8a1f5cbd7f0e0f`
- Legacy NOTORIA V1 source commit: `8486a7d577631fca6434fcac33217c870d629c9d`
- Existing Claude agent definitions: branch `claude/aspar-social-media-pipeline-756wh`
