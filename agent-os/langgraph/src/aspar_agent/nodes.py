from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .state import RunState, SourceRecord
from .tools import resolve_brand_tool, source_lock_tool


VISUAL_MARKERS = (
    "image",
    "visual",
    "carousel",
    "carrousel",
    "cover",
    "couverture",
    "design",
    "canva",
    "portrait",
    "photo",
    "thumbnail",
)

CONTENT_MARKERS = (
    "tiktok",
    "instagram",
    "linkedin",
    "post",
    "bio",
    "content",
    "contenu",
    "copy",
)

TECH_MARKERS = (
    "langgraph",
    "langchain",
    "python",
    "api",
    "mcp",
    "github",
    "supabase",
    "odoo",
)

CLAIM_MARKERS = (
    "statistic",
    "statistique",
    "kpi",
    "case study",
    "étude de cas",
    "claiming",
    "affirme",
    "chiffre",
)


def _trace(state: RunState, name: str) -> list[str]:
    return [*state.get("trace", []), name]


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _requires_verified_claim(text: str) -> bool:
    if re.search(r"\b\d+(?:[.,]\d+)?\s*%", text):
        return True
    return _contains_any(text, CLAIM_MARKERS)


class NodeFactory:
    """Build graph nodes bound to the repository root used for local canonical files."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    def intake(self, state: RunState) -> dict[str, Any]:
        request = state.get("request", "").strip()
        return {
            "task": state.get("task") or request,
            "output_contract": state.get("output_contract")
            or "structured execution-ready result",
            "external_sources": state.get("external_sources", []),
            "context": state.get("context", {}),
            "decision_criteria": state.get(
                "decision_criteria",
                [
                    "use canonical sources before execution",
                    "do not invent missing facts or assets",
                    "stop on unresolved source conflict",
                ],
            ),
            "assumptions": state.get("assumptions", []),
            "stop_conditions": state.get(
                "stop_conditions",
                [
                    "required canonical source is missing",
                    "canonical sources conflict",
                    "verified evidence is missing for a factual claim",
                ],
            ),
            "conflicts": state.get("conflicts", []),
            "trace": _trace(state, "intake"),
        }

    def classify(self, state: RunState) -> dict[str, Any]:
        text = state.get("request", "").casefold()
        requires_visual_assets = _contains_any(text, VISUAL_MARKERS)
        requires_verified_claim = _requires_verified_claim(text)

        if _contains_any(text, TECH_MARKERS):
            domain = "tech"
        elif requires_visual_assets:
            domain = "design"
        elif _contains_any(text, CONTENT_MARKERS):
            domain = "content"
        else:
            domain = "business"

        return {
            "domain": domain,
            "requires_visual_assets": requires_visual_assets,
            "requires_verified_claim": requires_verified_claim,
            "trace": _trace(state, "classify"),
        }

    def resolve_role(self, state: RunState) -> dict[str, Any]:
        roles = {
            "tech": "ASPAR systems architect",
            "design": "senior brand and editorial design operator",
            "content": "personal-brand and content strategist",
            "business": "business builder and operator",
        }
        return {
            "role": roles.get(state.get("domain", "business"), "business builder and operator"),
            "trace": _trace(state, "resolve_role"),
        }

    def resolve_brand(self, state: RunState) -> dict[str, Any]:
        resolution = resolve_brand_tool.invoke({"request": state.get("request", "")})
        return {
            "brand": str(resolution["brand"]),
            "trace": _trace(state, "resolve_brand"),
        }

    def source_router(self, state: RunState) -> dict[str, Any]:
        required: list[SourceRecord] = []
        brand = state.get("brand")

        if brand == "majdi_personal_brand":
            required.append(
                {
                    "id": "majdi_source_lock",
                    "kind": "local_file",
                    "path": "brands/majdi-personal-brand/SOURCE_LOCK.md",
                    "status": "required",
                }
            )
            if state.get("requires_visual_assets"):
                required.extend(
                    [
                        {
                            "id": "majdi_canva_brand_kit",
                            "kind": "canva_brand_kit",
                            "status": "required",
                        },
                        {
                            "id": "majdi_drive_assets",
                            "kind": "drive_asset_source",
                            "status": "required",
                        },
                    ]
                )

        if state.get("requires_verified_claim"):
            required.append(
                {
                    "id": "verified_claim_evidence",
                    "kind": "evidence",
                    "status": "required",
                }
            )

        return {
            "required_sources": required,
            "trace": _trace(state, "source_router"),
        }

    def retrieve_context(self, state: RunState) -> dict[str, Any]:
        resolved: list[SourceRecord] = []
        context = dict(state.get("context", {}))
        external_by_id = {
            source.get("id"): source
            for source in state.get("external_sources", [])
            if source.get("id")
        }

        for source in state.get("required_sources", []):
            source_id = source.get("id", "")
            kind = source.get("kind")

            if kind == "local_file":
                relative_path = source.get("path", "")
                path = self.repo_root / relative_path
                if path.is_file():
                    content = path.read_text(encoding="utf-8")
                    if content.strip():
                        record: SourceRecord = {
                            **source,
                            "status": "resolved",
                            "content": content,
                        }
                        resolved.append(record)
                        context[source_id] = {
                            "kind": kind,
                            "path": relative_path,
                            "status": "resolved",
                        }
                continue

            external = external_by_id.get(source_id)
            if external and external.get("status") == "resolved":
                resolved.append({**source, **external, "status": "resolved"})
                context[source_id] = {
                    "kind": external.get("kind", kind),
                    "status": "resolved",
                    "metadata": external.get("metadata", {}),
                }

        return {
            "resolved_sources": resolved,
            "context": context,
            "trace": _trace(state, "retrieve_context"),
        }

    def validate(self, state: RunState) -> dict[str, Any]:
        required_ids = [source["id"] for source in state.get("required_sources", [])]
        resolved_ids = [source["id"] for source in state.get("resolved_sources", [])]
        missing = [source_id for source_id in required_ids if source_id not in resolved_ids]

        return {
            "missing_sources": missing,
            "rationale": (
                "All required canonical inputs are resolved."
                if not missing and not state.get("conflicts")
                else "Execution is blocked until canonical inputs and conflicts are resolved."
            ),
            "trace": _trace(state, "validate"),
        }

    def source_lock(self, state: RunState) -> dict[str, Any]:
        required_ids = [source["id"] for source in state.get("required_sources", [])]
        resolved_ids = [source["id"] for source in state.get("resolved_sources", [])]
        decision = source_lock_tool.invoke(
            {
                "required_source_ids": required_ids,
                "resolved_source_ids": resolved_ids,
                "conflicts": state.get("conflicts", []),
            }
        )
        return {
            "source_lock_status": str(decision["status"]),
            "missing_sources": list(decision["missing_sources"]),
            "stop_reason": str(decision["reason"]),
            "trace": _trace(state, "source_lock"),
        }

    def plan(self, state: RunState) -> dict[str, Any]:
        plan = [
            f"Execute task as {state.get('role', 'operator')}",
            f"Respect output contract: {state.get('output_contract', '')}",
            "Use only resolved canonical sources and supplied verified evidence",
            "Run QA before any downstream side effect",
        ]
        return {"plan": plan, "trace": _trace(state, "plan")}

    def execute(self, state: RunState) -> dict[str, Any]:
        result = {
            "status": "READY_FOR_EXECUTOR",
            "mode": "preflight_only",
            "brand": state.get("brand"),
            "domain": state.get("domain"),
            "task": state.get("task"),
            "output_contract": state.get("output_contract"),
            "resolved_source_ids": [
                source["id"] for source in state.get("resolved_sources", [])
            ],
        }
        return {"result": result, "trace": _trace(state, "execute")}

    def qa(self, state: RunState) -> dict[str, Any]:
        issues: list[str] = []
        if state.get("source_lock_status") != "PASS":
            issues.append("source_lock_not_passed")
        if state.get("result", {}).get("status") != "READY_FOR_EXECUTOR":
            issues.append("execution_contract_not_ready")
        if not state.get("output_contract"):
            issues.append("missing_output_contract")

        return {
            "qa_status": "PASS" if not issues else "FAIL",
            "qa_issues": issues,
            "trace": _trace(state, "qa"),
        }

    def writeback(self, state: RunState) -> dict[str, Any]:
        status = "PASS" if state.get("source_lock_status") == "PASS" else "STOP"
        writeback = {
            "status": status,
            "brand": state.get("brand"),
            "domain": state.get("domain"),
            "source_lock_status": state.get("source_lock_status"),
            "qa_status": state.get("qa_status", "NOT_RUN"),
            "missing_sources": state.get("missing_sources", []),
            "stop_reason": state.get("stop_reason", ""),
        }
        return {"writeback": writeback, "trace": _trace(state, "writeback")}
