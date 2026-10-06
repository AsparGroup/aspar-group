import unittest

from shared.worker.template import _normalize_input_key, create_worker_app


class WorkerTemplateTestCase(unittest.TestCase):
    def test_normalize_input_key_for_s3_uri(self) -> None:
        self.assertEqual(_normalize_input_key("s3://notoria/jobs/a/input.wav"), "jobs/a/input.wav")

    def test_create_worker_app_has_standard_routes(self) -> None:
        app = create_worker_app("tts-test", version="1.0.0")
        paths = {route.path for route in app.router.routes}
        self.assertIn("/health", paths)
        self.assertIn("/generate", paths)
        self.assertIn("/status", paths)
        self.assertIn("/metrics", paths)


if __name__ == "__main__":
    unittest.main()
