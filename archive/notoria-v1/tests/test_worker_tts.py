import importlib.util
import tempfile
import unittest
from pathlib import Path

from shared.schemas import JobRequest

MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "worker-tts" / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("worker_tts_main", MODULE_PATH)
WORKER_TTS_MAIN = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER_TTS_MAIN)


class WorkerTTSTestCase(unittest.TestCase):
    def test_tts_processor_requires_voice_id(self) -> None:
        payload = JobRequest(avatar_id="av", script="bonjour", language="fr", format="wav", params={})
        with tempfile.TemporaryDirectory() as td:
            output, extra, errors = WORKER_TTS_MAIN._tts_processor(payload, Path(td), Path(td))
        self.assertTrue(str(output).endswith("voice.wav"))
        self.assertEqual(extra, {})
        self.assertIn("missing_required_param:voice_id", errors)

    def test_fake_tts_backend_writes_wav(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "voice.wav"
            WORKER_TTS_MAIN.FakeTTSBackend().synthesize("hello world", "voice_a", out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 44)

    def test_xtts_stub_backend_writes_wav(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "voice.wav"
            WORKER_TTS_MAIN.XTTSStubBackend().synthesize("hello world", "voice_a", out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 44)


if __name__ == "__main__":
    unittest.main()
