import unittest
import uuid

from shared.utils.ids import new_job_id


class IdsTestCase(unittest.TestCase):
    def test_new_job_id_is_uuid_v4(self) -> None:
        generated = new_job_id()
        parsed = uuid.UUID(generated)
        self.assertEqual(parsed.version, 4)


if __name__ == "__main__":
    unittest.main()
