import importlib.util
import tempfile
import unittest
from pathlib import Path

from shared.schemas import JobRequest

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "worker-video" / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("worker_video_main", MODULE_PATH)
WORKER_VIDEO_MAIN = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER_VIDEO_MAIN)


class WorkerVideoTestCase(unittest.TestCase):
    def test_video_processor_uses_script_as_prompt(self) -> None:
        payload = JobRequest(avatar_id="av", script="city skyline", language="en", format="mp4", params={})
        with tempfile.TemporaryDirectory() as td:
            output, extra, errors = WORKER_VIDEO_MAIN._video_processor(payload, Path(td), Path(td))
        self.assertTrue(str(output).endswith("broll.mp4"))
        self.assertEqual(errors, [])
        self.assertEqual(extra["prompt"], "city skyline")

    def test_video_processor_rejects_invalid_duration(self) -> None:
        payload = JobRequest(
            avatar_id="av",
            script="scene",
            language="en",
            format="mp4",
            params={"duration": 0, "prompt": "scene"},
        )
        with tempfile.TemporaryDirectory() as td:
            _output, _extra, errors = WORKER_VIDEO_MAIN._video_processor(payload, Path(td), Path(td))
        self.assertIn("invalid_param:duration_must_be_positive", errors)

    def test_fake_video_backend_writes_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "broll.mp4"
            WORKER_VIDEO_MAIN.FakeVideoBackend().render("prompt", None, 3.0, "16:9", out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 8)


if __name__ == "__main__":
    unittest.main()
