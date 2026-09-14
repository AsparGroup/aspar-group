from types import SimpleNamespace

import pytest

from aspar_agent.deepseek_worker import DeepSeekWorkerError, run_deepseek_worker


class _FakeChatCompletions:
    def __init__(self, text: str):
        self._text = text

    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._text))]
        )


class _FakeChat:
    def __init__(self, text: str):
        self.completions = _FakeChatCompletions(text)


class _FakeOpenAIClient:
    def __init__(self, text: str = "ok"):
        self.chat = _FakeChat(text)


def test_run_deepseek_worker_raises_without_api_key_and_without_injected_client(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(DeepSeekWorkerError):
        run_deepseek_worker("Test task")


def test_run_deepseek_worker_calls_the_injected_client_and_marks_output_unverified():
    fake_client = _FakeOpenAIClient(text="Brouillon de réponse.")

    result = run_deepseek_worker(
        "Rédige un brouillon",
        context="Contexte réel fourni explicitement.",
        client=fake_client,
    )

    assert result["status"] == "DRAFT_PRODUCED"
    assert result["output"] == "Brouillon de réponse."
    assert result["verification_required"] is True


def test_run_deepseek_worker_never_needs_a_real_network_call_or_key_when_client_injected(monkeypatch):
    """Proves the worker is fully testable without NVIDIA_API_KEY set, exactly
    like run_executor — CI never needs a real key to stay green."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    fake_client = _FakeOpenAIClient(text="ok")

    result = run_deepseek_worker("Test task", client=fake_client)

    assert result["status"] == "DRAFT_PRODUCED"
