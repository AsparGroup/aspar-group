"""Failover wrapper around `executor.run_executor`: if the primary LLM call
fails for ANY reason (missing key, quota, rate limit, network error — not
just a missing-key ExecutorError), DeepSeek (via `deepseek_worker.py`,
NVIDIA Build's free tier) takes over the same task automatically.

This is a pipeline-level continuity mechanism, not a way to resume THIS
Claude Code session — it cannot take over this conversation, push commits
as Claude Code, or drive tools. What it does is keep the LangGraph
execution step itself from hard-failing when one provider is unavailable,
so a scheduled/automated run of the graph (or a resumed run in a future
session) doesn't lose an execution step just because one provider is down.

A fallback result is always tagged `verification_required: True` — a
result served by the backup provider is read like an unverified Notion
field, never treated as final until a human or the primary path confirms
it (same discipline as ADR 0004).
"""

from __future__ import annotations

from typing import Any

from aspar_agent.deepseek_worker import run_deepseek_worker
from aspar_agent.executor import ExecutorError, _build_user_prompt, run_executor


def run_executor_resilient(
    gate_result: dict[str, Any],
    *,
    model: str = "gpt-4.1",
    max_tokens: int = 2048,
    client: Any | None = None,
    deepseek_client: Any | None = None,
) -> dict[str, Any]:
    """Try the primary executor first; on ANY failure, fall back to the
    DeepSeek worker with the same task/context. Raises ExecutorError only
    if BOTH providers fail — the caller then knows execution genuinely
    could not happen, not just that one provider had a bad day.

    A gate result that did not PASS is never a provider failure — it is a
    deliberate governance stop, and DeepSeek must never fall back around
    it. That case is left to `run_executor`'s own check, untouched.
    """
    if gate_result.get("writeback", {}).get("status") != "PASS":
        return run_executor(gate_result, model=model, max_tokens=max_tokens, client=client)

    try:
        return run_executor(gate_result, model=model, max_tokens=max_tokens, client=client)
    except Exception as primary_error:  # noqa: BLE001 - deliberately broad: any provider failure triggers failover
        try:
            fallback = run_deepseek_worker(
                task=gate_result.get("task", gate_result.get("request", "")),
                context=_build_user_prompt(gate_result),
                client=deepseek_client,
            )
        except Exception as fallback_error:  # noqa: BLE001 - mirror the broad primary catch: any fallback failure means genuine outage
            raise ExecutorError(
                f"Primary executor failed ({primary_error!s}) and the DeepSeek "
                f"fallback also failed ({fallback_error!s}) — no provider could "
                "run this task."
            ) from fallback_error

        return {
            "status": "EXECUTED_VIA_FALLBACK",
            "provider": "deepseek_fallback",
            "primary_provider_error": str(primary_error),
            "model": fallback["model"],
            "output": fallback["output"],
            "brand": gate_result.get("brand"),
            "domain": gate_result.get("domain"),
            "verification_required": True,
        }
