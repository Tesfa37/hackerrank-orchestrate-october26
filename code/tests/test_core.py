import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import IdentityIndex, Observation, serialize_steps, validate_citations, validate_output


def step(phase, operation, state, resource="account_custom", evidence=""):
    return {"step_no": 1, "phase": phase, "system_id": "account_service", "resource_id": resource,
            "operation": operation, "state": state, "evidence_id": evidence}


def row(status="INCOMPLETE", steps=None):
    if steps is None:
        steps = [step("FINDING", "REPORT_REMAINING_RECORD", "PRESENT", evidence="file_custom"),
                 step("REMEDIATION", "DELETE_RECORD", "ABSENT"),
                 step("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT")]
    return {"case_id": "case_custom", "deletion_status": status,
            "steps_json": json.dumps(serialize_steps(steps))}


REQUESTS = [{"case_id": "case_custom", "audit_at": "2026-09-10T12:00:00Z"}]


class CoreTests(unittest.TestCase):
    def test_future_catalog_join_cannot_prove_a_past_observation(self):
        from audit_core import Observation
        observation = Observation("identity_service", "tombstone_fixture", "ACCOUNT_TOMBSTONE", "REDACTED",
                                  "image", "2026-09-10T10:00:00Z", "2026-09-10T10:00:00Z",
                                  {"subject"}, {"_catalog_event_time": "2026-09-10T12:00:00Z"})
        self.assertFalse(observation.eligible("2026-09-10T11:00:00Z"))
        self.assertTrue(observation.eligible("2026-09-10T13:00:00Z"))
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

    def test_identity_history_rolls_back_all_future_fields_and_keeps_names_separate(self):
        identities = [
            {"user_id": "subject-a", "email": "future@example.org", "name": "Shared Name", "phone": "+1 555 123 4567", "email_hash": "futurehash"},
            {"user_id": "subject-b", "email": "other@example.org", "name": "Shared Name", "phone": "+1 555 999 9999", "email_hash": "otherhash"},
        ]
        history = [
            {"user_id": "subject-a", "field_name": field, "old_value": old, "new_value": new, "event_time": "2026-10-20T00:00:00Z"}
            for field, old, new in [("email", "old@example.org", "future@example.org"),
                                    ("phone", "+1 555 765 4321", "+1 555 123 4567"),
                                    ("email_hash", "oldhash", "futurehash")]
        ]
        subject = IdentityIndex(identities, history).resolve("old@example.org", "2026-10-10T00:00:00Z")
        self.assertEqual(subject.identifiers, {"subject-a", "old@example.org", "15557654321", "oldhash"})
        self.assertNotIn("other@example.org", subject.identifiers)
        with self.assertRaises(ValueError):
            IdentityIndex(identities, history).resolve("Shared Name", "2026-10-10T00:00:00Z")

    def test_unknown_history_fields_do_not_become_identifiers(self):
        identities = [{"user_id": "subject-a", "email": "person@example.org", "name": "Person"}]
        history = [{"user_id": "subject-a", "field_name": "marketing_preferences", "old_value": "someone@example.org", "new_value": "newsletter", "event_time": "2026-01-01T00:00:00Z"}]
        subject = IdentityIndex(identities, history).resolve("person@example.org", "2026-10-10T00:00:00Z")
        self.assertNotIn("someone@example.org", subject.identifiers)

    def test_complete_requires_nonempty_verification(self):
        with self.assertRaises(ValueError):
            validate_output([row("COMPLETE", [])], REQUESTS)

    def test_incomplete_requires_supported_remediation_and_verification(self):
        validate_output([row()], REQUESTS)
        original = json.loads(row()["steps_json"])
        for omitted in range(3):
            with self.subTest(omitted=omitted), self.assertRaises(ValueError):
                validate_output([row(steps=original[:omitted] + original[omitted + 1:])], REQUESTS)
        wrong_verification = [dict(s) for s in original]
        wrong_verification[-1]["resource_id"] = "unrelated_resource"
        with self.assertRaises(ValueError):
            validate_output([row(steps=wrong_verification)], REQUESTS)

    def test_exposed_pii_requires_redaction_or_anonymization(self):
        original = json.loads(row()["steps_json"])
        original[0]["operation"] = "REPORT_EXPOSED_PII"
        with self.assertRaises(ValueError):
            validate_output([row(steps=original)], REQUESTS)
        original[1].update(operation="REDACT_RECORD", state="REDACTED")
        original[2].update(operation="VERIFY_RECORD_REDACTED", state="REDACTED")
        validate_output([row(steps=original)], REQUESTS)

    def test_step_types_duplicate_keys_and_duplicate_steps_are_rejected(self):
        original = row()
        for field, bad in [("step_no", True), ("system_id", 123), ("evidence_id", ["file_custom"]), ("resource_id", "")]:
            changed = json.loads(original["steps_json"])
            changed[0][field] = bad
            changed_row = dict(original, steps_json=json.dumps(changed))
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_output([changed_row], REQUESTS)
        duplicate = dict(original, steps_json=original["steps_json"].replace('"phase": "FINDING"', '"phase": "FINDING", "phase": "FINDING"', 1))
        with self.assertRaises(ValueError):
            validate_output([duplicate], REQUESTS)
        changed = json.loads(original["steps_json"])
        changed.insert(1, dict(changed[0]))
        for number, current in enumerate(changed, 1):
            current["step_no"] = number
        with self.assertRaises(ValueError):
            validate_output([dict(original, steps_json=json.dumps(changed))], REQUESTS)

    def test_citation_validation_checks_identifiers_capture_and_observation_cutoff(self):
        manifest = [{"file_id": "file_custom", "captured_at": "2026-09-10T11:00:00Z"}]
        validate_citations([row()], REQUESTS, manifest)
        for records in ([], [{"file_id": "file_custom", "captured_at": "2026-09-10T13:00:00Z"}]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                validate_citations([row()], REQUESTS, records)
        observation = Observation("account_service", "account_custom", "USER_PROFILE", "PRESENT", "file_custom",
                                  "2026-09-10T11:00:00Z", "2026-09-10T13:00:00Z")
        with self.assertRaises(ValueError):
            validate_citations([row()], REQUESTS, manifest, observations=[observation])

    def test_activity_and_audit_citations_are_timed_without_trusting_reported_results(self):
        current = row()
        current["steps_json"] = current["steps_json"].replace("file_custom", "activity_custom")
        activities = [{"activity_id": "activity_custom", "event_time": "2026-09-10T11:00:00Z", "resource_id": "account_custom", "reported_result": "SUCCESS"}]
        validate_citations([current], REQUESTS, [], activities=activities)
        activities[0]["event_time"] = "2026-09-10T13:00:00Z"
        with self.assertRaises(ValueError):
            validate_citations([current], REQUESTS, [], activities=activities)
        current["steps_json"] = current["steps_json"].replace("activity_custom", "audit_custom")
        validate_citations([current], REQUESTS, [], history=[{"audit_id": "audit_custom", "event_time": "2026-09-10T11:00:00Z"}])


if __name__ == "__main__":
    unittest.main()
