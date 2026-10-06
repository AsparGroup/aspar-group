import importlib.util
import tempfile
import unittest
from pathlib import Path

from shared.schemas import JobRequest

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "worker-enhance" / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("worker_enhance_main", MODULE_PATH)
WORKER_ENHANCE_MAIN = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER_ENHANCE_MAIN)


class WorkerEnhanceTestCase(unittest.TestCase):
    def test_requires_video_uri(self) -> None:
        payload = JobRequest(avatar_id="av", script="x", language="en", format="mp4", params={})
        with tempfile.TemporaryDirectory() as td:
            _output, _extra, _metrics, errors = WORKER_ENHANCE_MAIN._enhance_processor(payload, Path(td), Path(td))
        self.assertIn("missing_required_param:video_uri", errors)

    def test_processor_outputs_flags(self) -> None:
        payload = JobRequest(
            avatar_id="av",
            script="x",
            language="en",
            format="mp4",
            params={"video_uri": "s3://notoria/jobs/1/video.mp4", "enable_upscale": True, "enable_face_restore": True},
        )
        with tempfile.TemporaryDirectory() as td:
            output, _extra, metrics, errors = WORKER_ENHANCE_MAIN._enhance_processor(payload, Path(td), Path(td))
        self.assertEqual(errors, [])
        self.assertTrue(str(output).endswith("enhanced.mp4"))
        self.assertTrue(metrics["enable_upscale"])
        self.assertTrue(metrics["enable_face_restore"])

    def test_fake_backend_writes_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "enhanced.mp4"
            WORKER_ENHANCE_MAIN.FakeEnhanceBackend().enhance("s3://notoria/in.mp4", True, False, out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 8)


if __name__ == "__main__":
    unittest.main()
