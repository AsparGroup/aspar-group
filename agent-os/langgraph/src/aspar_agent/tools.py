from __future__ import annotations

from langchain.tools import tool


def _contains_any(text: str, values: tuple[str, ...]) -> bool:
    return any(value in text for value in values)


@tool("resolve_brand")
def resolve_brand_tool(request: str) -> dict[str, str]:
    """Resolve the canonical ASPAR brand/domain owner for a user request."""
    text = request.casefold()

    if "aspar solutions" in text:
        return {"brand": "aspar_solutions"}
    if "aspar building" in text:
        return {"brand": "aspar_building"}
    if "aspar franchise" in text:
        return {"brand": "aspar_franchise"}
    if "aspar business" in text:
        return {"brand": "aspar_business"}

    personal_markers = (
        "majdi",
        "personal brand",
        "personal branding",
        "tiktok",
        "instagram",
        "linkedin",
        "bio",
        "profil",
        "profile",
    )
    if _contains_any(text, personal_markers):
        return {"brand": "majdi_personal_brand"}

    if "aspar" in text:
        return {"brand": "aspar_group"}

    return {"brand": "unscoped"}


@tool("evaluate_source_lock")
def source_lock_tool(
    required_source_ids: list[str],
    resolved_source_ids: list[str],
    conflicts: list[str] | None = None,
) -> dict[str, object]:
    """Evaluate whether all canonical sources required for a run are resolved."""
    conflicts = conflicts or []
    resolved = set(resolved_source_ids)
    missing = [source_id for source_id in required_source_ids if source_id not in resolved]

    if conflicts:
        return {
            "status": "STOP",
            "missing_sources": missing,
            "reason": "canonical_source_conflict",
        }
    if missing:
        return {
            "status": "STOP",
            "missing_sources": missing,
            "reason": "missing_canonical_sources",
        }

    return {"status": "PASS", "missing_sources": [], "reason": ""}
