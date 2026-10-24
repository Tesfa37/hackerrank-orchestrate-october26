import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_client import GeminiClient, MissingModelResult


class ModelClientTests(unittest.TestCase):
    def test_content_changes_cache_key(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), prepare=True)
            one = client.job("intent", [{"text": "Delete my account"}], {"type": "object"})
            two = client.job("intent", [{"text": "Keep my account"}], {"type": "object"})
            self.assertNotEqual(one["key"], two["key"])
            self.assertNotIn("api_key", one)

    def test_missing_offline_result_is_not_an_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), offline=True)
            with self.assertRaises(MissingModelResult):
                client.request("intent", [{"text": "Delete my account"}], {"type": "object"})

    def test_prepare_records_pending_without_fake_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), prepare=True)
            self.assertIsNone(client.request("intent", [{"text": "Delete my account"}], {"type": "object"}))
            self.assertEqual(len(client.pending), 1)


if __name__ == "__main__":
    unittest.main()
