import unittest
from uuid import UUID

from pydantic import ValidationError

from shared.schemas import JobRequest, JobResult, ServiceHealth


class CommonSchemasTestCase(unittest.TestCase):
    def test_job_request_generates_uuid_when_missing(self) -> None:
        data = JobRequest(avatar_id="av_1", script="hello world", language="fr", format="mp4", params={"voice": "a"})
        parsed = UUID(data.job_id)
        self.assertEqual(parsed.version, 4)

    def test_job_result_rejects_invalid_status(self) -> None:
        with self.assertRaises(ValidationError):
            JobResult(job_id="jid", status="pending", outputs={}, metrics={}, errors=[])

    def test_service_health_payload(self) -> None:
        health = ServiceHealth(service_name="worker-tts", ok=True, gpu={"name": "A10"}, version="1.2.3")
        self.assertTrue(health.ok)
        self.assertEqual(health.service_name, "worker-tts")


if __name__ == "__main__":
    unittest.main()
