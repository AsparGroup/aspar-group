import sys
import unittest
from pathlib import Path

from shared.schemas import JobRequest

APP_ROOT = Path(__file__).resolve().parents[1] / "services" / "orchestrator-api"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app import main as ORCH  # noqa: E402


class OrchestratorPipelineTestCase(unittest.TestCase):
    def test_script_agent_stub_returns_timing_map(self) -> None:
        spoken_script, timing_map = ORCH._script_agent_stub("hello world")
        self.assertEqual(spoken_script, "hello world")
        self.assertGreaterEqual(len(timing_map), 2)
        self.assertIn("start_s", timing_map[0])

    def test_s3_uri_from_outputs(self) -> None:
        uri = ORCH._s3_uri_from_outputs({"bucket": "notoria", "object_key": "jobs/j1/a.mp4"})
        self.assertEqual(uri, "s3://notoria/jobs/j1/a.mp4")

    def test_run_pipeline_delivery_happy_path(self) -> None:
        def fake_dispatch(_db, category, payload, _step):
            base = {
                "outputs": {
                    "bucket": "notoria",
                    "object_key": f"jobs/{payload['job_id']}/{category}/out.bin",
                    "presigned_url": f"http://minio/{category}/{payload['job_id']}",
                },
                "metrics": {},
                "errors": [],
            }
            if category == "lipsync":
                base["metrics"] = {"av_drift_ms": 10, "lipsync_score": 0.95}
            if category == "qa":
                base["outputs"]["qa_passed"] = True
            return base, {"service": f"{category}_svc", "retry": 0, "attempts": []}

        original = ORCH._dispatch_with_routing
        ORCH._dispatch_with_routing = fake_dispatch
        try:
            payload = JobRequest(avatar_id="av", script="hello", language="fr", format="mp4", params={})
            result = ORCH._run_pipeline(payload, db=None)  # type: ignore[arg-type]
        finally:
            ORCH._dispatch_with_routing = original

        self.assertEqual(result.status, "completed")
        self.assertIn("delivery", result.outputs)
        self.assertIn("enhanced_mp4", result.outputs["delivery"]["final_assets_urls"])


if __name__ == "__main__":
    unittest.main()
