import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import IdentityIndex, serialize_steps, validate_output


class CoreTests(unittest.TestCase):
    def test_historical_email_and_future_identity_rollback(self):
        identities = [{"user_id": "subject-a", "email": "future@example.org", "name": "Shared Name", "phone": "222", "email_hash": "futurehash", "updated_at": "2026-10-20T00:00:00Z"}]
        history = [{"audit_id": "a1", "user_id": "subject-a", "field_name": "email", "old_value": "old@example.org", "new_value": "future@example.org", "event_time": "2026-10-20T00:00:00Z"}]
        subject = IdentityIndex(identities, history).resolve("OLD@EXAMPLE.ORG", "2026-10-10T00:00:00Z")
        self.assertEqual(subject.user_id, "subject-a")
        self.assertIn("old@example.org", subject.identifiers)
        self.assertNotIn("future@example.org", subject.identifiers)

    def test_canonical_operations_and_numbering(self):
        steps = [{"phase": "REMEDIATION", "system_id": "a", "resource_id": "r", "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""}, {"phase": "FINDING", "system_id": "z", "resource_id": "flow", "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE", "evidence_id": "e1"}, {"phase": "REMEDIATION", "system_id": "z", "resource_id": "flow", "operation": "DISABLE_DATA_FLOW", "state": "DISABLED", "evidence_id": ""}]
        actual = serialize_steps(steps)
        self.assertEqual([s["operation"] for s in actual], ["REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "DELETE_RECORD"])
        self.assertEqual([s["step_no"] for s in actual], [1, 2, 3])
        self.assertEqual(len(actual[0]), 7)

    def test_non_deletion_requires_empty_steps(self):
        with self.assertRaises(ValueError):
            validate_output([{"case_id": "c", "deletion_status": "NOT_APPLICABLE", "steps_json": '[{}]'}], [{"case_id": "c"}])


if __name__ == "__main__":
    unittest.main()
