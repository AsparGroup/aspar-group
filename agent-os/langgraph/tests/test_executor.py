from types import SimpleNamespace

import pytest

from aspar_agent.executor import ExecutorError, run_executor


def _pass_gate_result(**overrides):
    result = {
        "writeback": {"status": "PASS"},
        "task": "Update Majdi Garbouj TikTok bio",
        "role": "personal-brand and content strategist",
        "domain": "content",
        "brand": "majdi_personal_brand",
        "output_contract": "structured execution-ready result",
        "plan": ["Execute task as content strategist"],
        "resolved_sources": [],
    }
    result.update(overrides)
    return result


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


def test_run_executor_rejects_a_gate_result_that_did_not_pass():
    with pytest.raises(ExecutorError):
        run_executor({"writeback": {"status": "STOP"}})


def test_run_executor_calls_the_injected_client_and_returns_executed_status():
    fake_client = _FakeOpenAIClient(text="Bio mise à jour.")

    result = run_executor(_pass_gate_result(), client=fake_client)

    assert result["status"] == "EXECUTED"
    assert result["output"] == "Bio mise à jour."
    assert result["brand"] == "majdi_personal_brand"
    assert result["domain"] == "content"


def test_run_executor_raises_without_api_key_and_without_injected_client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ExecutorError):
        run_executor(_pass_gate_result())
