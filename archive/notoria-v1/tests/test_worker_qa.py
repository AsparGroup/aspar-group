import importlib.util
import tempfile
import unittest
from pathlib import Path

from shared.schemas import JobRequest

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "worker-qa" / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("worker_qa_main", MODULE_PATH)
WORKER_QA_MAIN = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER_QA_MAIN)


class WorkerQATestCase(unittest.TestCase):
    def test_requires_final_cut_uri(self) -> None:
        payload = JobRequest(avatar_id="av", script="x", language="en", format="mp4", params={})
        with tempfile.TemporaryDirectory() as td:
            _output, _extra, _metrics, errors = WORKER_QA_MAIN._qa_processor(payload, Path(td), Path(td))
        self.assertIn("missing_required_param:final_cut_uri", errors)

    def test_qa_passes_when_rules_valid(self) -> None:
        payload = JobRequest(
            avatar_id="av",
            script="x",
            language="en",
            format="mp4",
            params={
                "final_cut_uri": "s3://notoria/jobs/1/final_cut.mp4",
                "av_drift_ms": 15,
                "lipsync_score": 0.95,
                "freeze_frame_detected": False,
                "blink_rate": 18,
            },
        )
        with tempfile.TemporaryDirectory() as td:
            output, extra, _metrics, errors = WORKER_QA_MAIN._qa_processor(payload, Path(td), Path(td))
            self.assertTrue(output.exists())
        self.assertEqual(errors, [])
        self.assertTrue(extra["qa_passed"])
        self.assertIsNone(extra["recommended_step_to_retry"])

    def test_qa_fails_and_recommends_retry_step(self) -> None:
        payload = JobRequest(
            avatar_id="av",
            script="x",
            language="en",
            format="mp4",
            params={
                "final_cut_uri": "s3://notoria/jobs/1/final_cut.mp4",
                "av_drift_ms": 80,
                "lipsync_score": 0.4,
                "freeze_frame_detected": False,
                "blink_rate": 18,
                "lipsync_threshold": 0.9,
            },
        )
        with tempfile.TemporaryDirectory() as td:
            _output, extra, _metrics, errors = WORKER_QA_MAIN._qa_processor(payload, Path(td), Path(td))
        self.assertFalse(extra["qa_passed"])
        self.assertEqual(extra["recommended_step_to_retry"], "lipsync")
        self.assertTrue(any(e.startswith("qa_rule_failed:") for e in errors))


if __name__ == "__main__":
    unittest.main()
