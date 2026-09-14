"""Second LangGraph-orchestrated worker — a free-tier LLM used purely for
research/drafting, running alongside the primary executor.

History: this started as a DeepSeek integration via the DeepSeek Harness
desktop app (abandoned: unfixable workspace-picker bug, GitHub Discussion
#352). Two intermediate providers were tried and reverted the same day
(2026-09-14) while chasing a free tier: NVIDIA Build's DeepSeek endpoint
(blocked by an account-verification gate with no timeline) and Google AI
Studio's Gemini (worked, but the CEO wants DeepSeek specifically, not a
substitute model). Landed back on DeepSeek's own official API
(platform.deepseek.com) — it has a genuine free tier (5M tokens, 30 days,
no credit card, confirmed 2026-09-14) that was simply never checked before
detouring through other providers. Reached through its OpenAI-compatible
endpoint, same as DSH's native "deepseek-official" provider.

Mirrors `executor.py`'s pattern deliberately (dependency-injectable client,
env-var key, no network/key needed for tests) so every provider is wired
the same way and stays swappable from one place.

Hard rule (ADR 0004 discipline, extended to this second model): this
worker's output is a DRAFT/RESEARCH aid, never a decision or a verified
fact. Every result is tagged `verification_required: True` and callers
must treat it exactly like an unverified Notion field — read it, never
act on it as ground truth for a price, a score, or a gate.
"""

from __future__ import annotations

import os
from typing import Any

DEEPSEEK_OFFICIAL_BASE_URL = "https://api.deepseek.com"

SECOND_AGENT_SYSTEM_PROMPT = """Tu es un agent de recherche et de rédaction pour ASPAR Group.

Règles strictes, non négociables :
- Tu n'inventes jamais un chiffre, un prix, un fait ou une source qui ne t'est pas donné explicitement dans le contexte fourni. Si une information manque, tu le dis, tu ne combles jamais le vide.
- Ta sortie est un brouillon de travail, jamais une décision actée ni une donnée vérifiée — elle sera relue par un humain ou par un autre agent avant tout usage.
- Tu ne traites aucune donnée client confidentielle au-delà de ce qui t'est explicitement fourni dans le contexte.
"""


class SecondAgentWorkerError(RuntimeError):
    """Raised when the second-agent worker cannot run (missing key, API failure)."""


def run_second_agent_worker(
    task: str,
    context: str = "",
    *,
    model: str = "deepseek-chat",
    max_tokens: int = 2048,
    client: Any | None = None,
) -> dict[str, Any]:
    """Call a second, parallel LangGraph-orchestrated agent for research or
    drafting tasks — DeepSeek's own official API (free tier) by default.

    `client` can be injected for testing (any object exposing
    `.chat.completions.create(...)` with the OpenAI SDK's response shape) —
    no real network call or API key is needed to exercise this function's
    logic, matching the pattern already used for `run_executor`.

    Reads `DEEPSEEK_API_KEY` from the environment — never pass a key as an
    argument or hardcode one; the CEO sets it directly in `.env`. This must
    be a NEW key generated at platform.deepseek.com/api_keys — the key
    pasted into chat on 2026-09-14 is permanently banned regardless of
    rotation and must never be reused here.
    """

    if client is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise SecondAgentWorkerError(
                "DEEPSEEK_API_KEY is not set — cannot call the second-agent worker. "
                "Generate a NEW key at platform.deepseek.com/api_keys (free tier: "
                "5M tokens, 30 days, no credit card) and set it directly in "
                "agent-os/langgraph/.env (never pasted into a chat)."
            )
        try:
            import openai
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise SecondAgentWorkerError(
                "The 'openai' package is required — add it to pyproject.toml dependencies."
            ) from exc
        client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_OFFICIAL_BASE_URL)

    user_prompt = f"Tâche : {task}\n\nContexte fourni (ne rien inventer au-delà) :\n{context or '(aucun contexte fourni)'}"

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SECOND_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    output_text = response.choices[0].message.content or ""

    return {
        "status": "DRAFT_PRODUCED",
        "model": model,
        "provider": "deepseek_official",
        "output": output_text,
        "verification_required": True,
    }
