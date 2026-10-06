import unittest

from pydantic import ValidationError

from shared.schemas.service_registry import RegistryServiceCreate


class RegistrySchemasTestCase(unittest.TestCase):
    def test_valid_registry_payload(self) -> None:
        payload = RegistryServiceCreate(
            service_name="xtts_local",
            category="tts",
            type="local",
            base_url="http://worker-tts:80",
            auth_type="none",
            endpoints={"run": "/v1/run"},
            limits={"timeout_s": 60},
            fallback_service="xtts_cloud",
            enabled=True,
        )
        self.assertEqual(payload.category.value, "tts")

    def test_invalid_category_raises(self) -> None:
        with self.assertRaises(ValidationError):
            RegistryServiceCreate(
                service_name="bad",
                category="speech",
                type="local",
                base_url="http://worker-tts:80",
                auth_type="none",
                endpoints={},
                limits={},
            )


if __name__ == "__main__":
    unittest.main()
