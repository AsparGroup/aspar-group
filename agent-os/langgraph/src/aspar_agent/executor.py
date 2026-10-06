"""Real execution layer for the ASPAR Agent pre-execution gate.

The LangGraph pipeline in `graph.py` only validates and gates a request
(source lock, QA, writeback) — it never reasons about the task itself.
Once the gate returns `status == "READY_FOR_EXECUTOR"`, this module is
the actual "executor": it calls a real LLM (OpenAI/ChatGPT by default)
with the resolved canonical sources and the ASPAR Agent persona rules,
and returns the model's answer.

Kept deliberately separate from `nodes.execute` so the existing gate
tests (`tests/test_preexecution_gate.py`) never need real network access
or an API key to stay green in CI.
"""

from __future__ import annotations

import os
from typing import Any

ASPAR_AGENT_SYSTEM_PROMPT = """Tu es ASPAR Agent, le copilote unique de l'entrepreneur ASPAR, de A à Z.

Règles strictes, non négociables :
- Tu ne mentionnes jamais un nom d'outil technique sous-jacent (jamais "Odoo", jamais le nom d'un LLM, jamais une marque d'application). Le client ne doit jamais apprendre quel outil tourne derrière toi.
- Tu es le seul intermédiaire visible entre le client et ses systèmes réels (caisse, pointeuse, campagnes). Les autres applications sont à consulter, jamais à manipuler directement par le client.
- Tu n'inventes jamais un fait, un chiffre, un prix ou un témoignage qui n'est pas dans les sources fournies. Si une information manque, tu le dis clairement plutôt que de deviner.
- Tu peux répondre en arabe tunisien professionnel si le client s'adresse à toi ainsi, ou en français/anglais sinon.
- Tu restes concentré sur l'exécution demandée : agir à la place du client (lancer une campagne, produire un document de pointeuse, envoyer un SMS), pas lui expliquer comment le faire lui-même.
"""


class ExecutorError(RuntimeError):
    """Raised when the executor cannot run (missing key, API failure)."""


def _build_user_prompt(gate_result: dict[str, Any]) -> str:
    sources = gate_result.get("resolved_sources", [])
    source_texts = "\n\n".join(
        f"[Source: {s.get('id')}]\n{s.get('content', '')}".strip()
        for s in sources
        if s.get("content")
    )
    plan = "\n".join(f"- {step}" for step in gate_result.get("plan", []))

    return f"""Tâche : {gate_result.get('task', gate_result.get('request', ''))}
Rôle à endosser : {gate_result.get('role', 'business builder and operator')}
Domaine : {gate_result.get('domain', 'business')}
Contrat de sortie attendu : {gate_result.get('output_contract', '')}

Plan validé par le portail de contrôle :
{plan}

Sources canoniques résolues (à utiliser exclusivement, ne rien inventer au-delà) :
{source_texts or '(aucune source externe requise pour cette tâche)'}

Exécute la tâche maintenant en respectant strictement les règles de ton system prompt."""


def run_executor(
    gate_result: dict[str, Any],
    *,
    model: str = "gpt-4.1",
    max_tokens: int = 2048,
    client: Any | None = None,
) -> dict[str, Any]:
    """Call an LLM (OpenAI/ChatGPT by default) with the gate's validated
    context and return a real result.

    `gate_result` is the final state dict returned by `graph.build_graph().invoke(...)`
    once `writeback.status == "PASS"`. Calling this on a STOP result is a
    programming error — callers must check the gate status first.

    `client` can be injected for testing (any object exposing
    `.chat.completions.create(...)` with the OpenAI SDK's response shape).
    Swap the default `model` (and the client construction below) to use a
    different provider — this is the only place a provider is chosen.
    """

    if gate_result.get("writeback", {}).get("status") != "PASS":
        raise ExecutorError(
            "run_executor called on a gate result that did not PASS — "
            "check writeback.status before executing."
        )

    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ExecutorError(
                "OPENAI_API_KEY is not set — cannot call the real executor. "
                "Set it in the environment (see .env.example)."
            )
        try:
            import openai
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise ExecutorError(
                "The 'openai' package is required — add it to pyproject.toml dependencies."
            ) from exc
        client = openai.OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": ASPAR_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(gate_result)},
        ],
    )

    output_text = response.choices[0].message.content or ""

    return {
        "status": "EXECUTED",
        "model": model,
        "output": output_text,
        "brand": gate_result.get("brand"),
        "domain": gate_result.get("domain"),
    }
