import importlib.util
import tempfile
import unittest
from pathlib import Path

from shared.schemas import JobRequest

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "worker-lipsync" / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("worker_lipsync_main", MODULE_PATH)
WORKER_LIPSYNC_MAIN = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER_LIPSYNC_MAIN)


class WorkerLipsyncTestCase(unittest.TestCase):
    def test_requires_avatar_and_voice_uris(self) -> None:
        payload = JobRequest(avatar_id="av", script="x", language="en", format="mp4", params={})
        with tempfile.TemporaryDirectory() as td:
            _output, _extra, _metrics, errors = WORKER_LIPSYNC_MAIN._lipsync_processor(payload, Path(td), Path(td))
        self.assertIn("missing_required_param:avatar_base_uri", errors)

    def test_lipsync_outputs_placeholder_metrics(self) -> None:
        payload = JobRequest(
            avatar_id="av",
            script="x",
            language="en",
            format="mp4",
            params={"avatar_base_uri": "s3://notoria/jobs/1/avatar_base.mp4", "voice_uri": "s3://notoria/jobs/1/voice.wav"},
        )
        with tempfile.TemporaryDirectory() as td:
            output, _extra, metrics, errors = WORKER_LIPSYNC_MAIN._lipsync_processor(payload, Path(td), Path(td))
        self.assertEqual(errors, [])
        self.assertTrue(str(output).endswith("avatar_lipsynced.mp4"))
        self.assertIn("lipsync_score", metrics)
        self.assertIn("av_drift_ms", metrics)


if __name__ == "__main__":
    unittest.main()
