from __future__ import annotations

import json
from pathlib import Path

from .graph import build_graph


REPO_ROOT = Path(__file__).resolve().parents[4]


def main() -> None:
    graph = build_graph(repo_root=REPO_ROOT)

    pass_result = graph.invoke(
        {
            "request": "Update Majdi Garbouj TikTok bio for his personal brand",
            "output_contract": "bio copy",
            "external_sources": [],
        },
        {"configurable": {"thread_id": "smoke-pass"}},
    )

    stop_result = graph.invoke(
        {
            "request": "Create a carousel image for Majdi Garbouj personal branding",
            "output_contract": "carousel storyboard",
            "external_sources": [],
        },
        {"configurable": {"thread_id": "smoke-stop"}},
    )

    assert pass_result["source_lock_status"] == "PASS"
    assert pass_result["qa_status"] == "PASS"
    assert pass_result["result"]["status"] == "READY_FOR_EXECUTOR"

    assert stop_result["source_lock_status"] == "STOP"
    assert "execute" not in stop_result["trace"]

    print(
        json.dumps(
            {
                "status": "ok",
                "pass_path": pass_result["source_lock_status"],
                "stop_path": stop_result["source_lock_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
