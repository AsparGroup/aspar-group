import json
from pathlib import Path

from aspar_agent.graph import build_graph
from aspar_agent.persistence import postgres_checkpointer
from aspar_agent.tools import resolve_brand_tool


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def invoke(request: str, **overrides):
    graph = build_graph(repo_root=REPO_ROOT)
    payload = {
        "request": request,
        "output_contract": "structured execution-ready result",
        "external_sources": [],
    }
    payload.update(overrides)
    return graph.invoke(
        payload,
        {"configurable": {"thread_id": overrides.get("thread_id", "test-thread")}},
    )


def test_repository_root_contains_canonical_majdi_source_lock():
    assert (REPO_ROOT / "brands/majdi-personal-brand/SOURCE_LOCK.md").is_file()


def test_langchain_brand_tool_resolves_majdi_personal_brand():
    assert resolve_brand_tool.name == "resolve_brand"
    result = resolve_brand_tool.invoke(
        {"request": "Update Majdi Garbouj personal branding bio on TikTok"}
    )
    assert result["brand"] == "majdi_personal_brand"


def test_text_only_majdi_task_passes_source_lock_and_reaches_qa_writeback():
    result = invoke("Update Majdi Garbouj TikTok bio for his personal brand")

    assert result["source_lock_status"] == "PASS"
    assert result["qa_status"] == "PASS"
    assert result["result"]["status"] == "READY_FOR_EXECUTOR"
    assert result["writeback"]["status"] == "PASS"
    assert "execute" in result["trace"]
    assert result["brand"] == "majdi_personal_brand"


def test_visual_majdi_task_stops_without_canva_and_drive_sources():
    result = invoke("Create a carousel image for Majdi Garbouj personal branding")

    assert result["source_lock_status"] == "STOP"
    assert "majdi_canva_brand_kit" in result["missing_sources"]
    assert "majdi_drive_assets" in result["missing_sources"]
    assert "plan" not in result["trace"]
    assert "execute" not in result["trace"]
    assert result["writeback"]["status"] == "STOP"


def test_visual_majdi_task_passes_when_canonical_external_sources_are_resolved():
    result = invoke(
        "Create a carousel image for Majdi Garbouj personal branding",
        external_sources=[
            {
                "id": "majdi_canva_brand_kit",
                "status": "resolved",
                "kind": "canva_brand_kit",
            },
            {
                "id": "majdi_drive_assets",
                "status": "resolved",
                "kind": "drive_asset_source",
            },
        ],
        thread_id="visual-pass",
    )

    assert result["source_lock_status"] == "PASS"
    assert result["missing_sources"] == []
    assert result["qa_status"] == "PASS"
    assert result["result"]["status"] == "READY_FOR_EXECUTOR"


def test_claim_request_stops_without_verified_evidence():
    result = invoke("Create a post claiming that 88% of startups fail in the first years")

    assert result["source_lock_status"] == "STOP"
    assert "verified_claim_evidence" in result["missing_sources"]
    assert "execute" not in result["trace"]


def test_langgraph_json_points_to_exported_graph():
    config = json.loads((PACKAGE_ROOT / "langgraph.json").read_text(encoding="utf-8"))
    assert config["dependencies"] == ["."]
    assert config["graphs"]["aspar_agent"] == "./src/aspar_agent/graph.py:graph"


def test_postgres_checkpointer_is_exposed_as_context_manager_factory():
    assert callable(postgres_checkpointer)
