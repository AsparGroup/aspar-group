"""Second LangGraph-orchestrated worker: DeepSeek via NVIDIA Build's free,
OpenAI-compatible endpoint — not the abandoned DeepSeek Harness desktop app
(unfixable upstream workspace-picker bug, GitHub Discussion #352).

Mirrors `executor.py`'s pattern deliberately (dependency-injectable client,
env-var key, no network/key needed for tests) so both providers are wired
the same way and stay swappable from one place.

Hard rule (ADR 0004 discipline, extended to this second model): this
worker's output is a DRAFT/RESEARCH aid, never a decision or a verified
fact. Every result is tagged `verification_required: True` and callers
must treat it exactly like an unverified Notion field — read it, never
act on it as ground truth for a price, a score, or a gate.
"""

from __future__ import annotations

import os
from typing import Any

NVIDIA_BUILD_BASE_URL = "https://integrate.api.nvidia.com/v1"

DEEPSEEK_WORKER_SYSTEM_PROMPT = """Tu es un agent de recherche et de rédaction pour ASPAR Group.

Règles strictes, non négociables :
- Tu n'inventes jamais un chiffre, un prix, un fait ou une source qui ne t'est pas donné explicitement dans le contexte fourni. Si une information manque, tu le dis, tu ne combles jamais le vide.
- Ta sortie est un brouillon de travail, jamais une décision actée ni une donnée vérifiée — elle sera relue par un humain ou par un autre agent avant tout usage.
- Tu ne traites aucune donnée client confidentielle au-delà de ce qui t'est explicitement fourni dans le contexte.
"""


class DeepSeekWorkerError(RuntimeError):
    """Raised when the DeepSeek worker cannot run (missing key, API failure)."""


def run_deepseek_worker(
    task: str,
    context: str = "",
    *,
    model: str = "deepseek-ai/deepseek-v3.1",
    max_tokens: int = 2048,
    client: Any | None = None,
) -> dict[str, Any]:
    """Call DeepSeek (via NVIDIA Build's free tier by default) as a second,
    parallel LangGraph-orchestrated agent for research/drafting tasks.

    `client` can be injected for testing (any object exposing
    `.chat.completions.create(...)` with the OpenAI SDK's response shape) —
    no real network call or API key is needed to exercise this function's
    logic, matching the pattern already used for `run_executor`.

    Reads `NVIDIA_API_KEY` from the environment — never pass a key as an
    argument or hardcode one; the CEO sets it directly in `.env`.
    """

    if client is None:
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise DeepSeekWorkerError(
                "NVIDIA_API_KEY is not set — cannot call the DeepSeek worker. "
                "Generate a key at build.nvidia.com and set it directly in "
                "agent-os/langgraph/.env (never pasted into a chat)."
            )
        try:
            import openai
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise DeepSeekWorkerError(
                "The 'openai' package is required — add it to pyproject.toml dependencies."
            ) from exc
        client = openai.OpenAI(api_key=api_key, base_url=NVIDIA_BUILD_BASE_URL)

    user_prompt = f"Tâche : {task}\n\nContexte fourni (ne rien inventer au-delà) :\n{context or '(aucun contexte fourni)'}"

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": DEEPSEEK_WORKER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    output_text = response.choices[0].message.content or ""

    return {
        "status": "DRAFT_PRODUCED",
        "model": model,
        "provider": "nvidia_build" if "nvidia" in NVIDIA_BUILD_BASE_URL else "deepseek_direct",
        "output": output_text,
        "verification_required": True,
    }
