from typing import Any

from typing_extensions import TypedDict


class SourceRecord(TypedDict, total=False):
    id: str
    kind: str
    status: str
    path: str
    content: str
    metadata: dict[str, Any]


class RunState(TypedDict, total=False):
    request: str
    role: str
    task: str
    domain: str
    brand: str
    context: dict[str, Any]
    decision_criteria: list[str]
    assumptions: list[str]
    rationale: str
    stop_conditions: list[str]
    output_contract: str
    required_sources: list[SourceRecord]
    external_sources: list[SourceRecord]
    resolved_sources: list[SourceRecord]
    missing_sources: list[str]
    conflicts: list[str]
    requires_visual_assets: bool
    requires_verified_claim: bool
    source_lock_status: str
    stop_reason: str
    plan: list[str]
    result: dict[str, Any]
    qa_status: str
    qa_issues: list[str]
    writeback: dict[str, Any]
    trace: list[str]
