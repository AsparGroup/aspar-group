from types import SimpleNamespace

import pytest

from aspar_agent.executor import ExecutorError
from aspar_agent.resilient_executor import run_executor_resilient


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
    def __init__(self, text: str = None, error: Exception = None):
        self._text = text
        self._error = error

    def create(self, **kwargs):
        if self._error:
            raise self._error
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._text))]
        )


class _FakeChat:
    def __init__(self, text: str = None, error: Exception = None):
        self.completions = _FakeChatCompletions(text=text, error=error)


class _FakeClient:
    def __init__(self, text: str = None, error: Exception = None):
        self.chat = _FakeChat(text=text, error=error)


def test_primary_success_never_touches_deepseek():
    primary = _FakeClient(text="Bio mise à jour.")
    result = run_executor_resilient(_pass_gate_result(), client=primary, deepseek_client="SHOULD_NOT_BE_USED")

    assert result["status"] == "EXECUTED"
    assert result["output"] == "Bio mise à jour."


def test_primary_quota_failure_falls_back_to_deepseek():
    primary = _FakeClient(error=RuntimeError("rate limit exceeded"))
    fallback = _FakeClient(text="Brouillon de secours.")

    result = run_executor_resilient(_pass_gate_result(), client=primary, deepseek_client=fallback)

    assert result["status"] == "EXECUTED_VIA_FALLBACK"
    assert result["provider"] == "deepseek_fallback"
    assert result["output"] == "Brouillon de secours."
    assert result["verification_required"] is True
    assert "rate limit exceeded" in result["primary_provider_error"]


def test_both_providers_failing_raises_executor_error():
    primary = _FakeClient(error=RuntimeError("primary down"))
    fallback = _FakeClient(error=RuntimeError("fallback down"))

    with pytest.raises(ExecutorError):
        run_executor_resilient(_pass_gate_result(), client=primary, deepseek_client=fallback)


def test_gate_not_passed_never_falls_back_around_governance():
    """A STOP gate result must raise exactly like run_executor alone would —
    DeepSeek must never execute a task the gate deliberately blocked."""
    stopped_gate = _pass_gate_result(writeback={"status": "STOP"})

    with pytest.raises(ExecutorError):
        run_executor_resilient(stopped_gate, client="SHOULD_NOT_BE_CALLED", deepseek_client="SHOULD_NOT_BE_CALLED")
