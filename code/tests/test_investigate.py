"""Diagnostic fixtures verify missing proof is classified, never fabricated."""
import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import IdentityIndex, Observation
from evidence import EvidenceStore
from investigate import diagnose, markdown, raw_primary_records


CUTOFF = "2026-09-10T12:00:00Z"
BEFORE = "2026-09-09T12:00:00Z"
AFTER = "2026-09-11T12:00:00Z"
REQUEST = {"case_id": "custom_request", "email": "person@example.org", "requested_at": "2026-09-08T12:00:00Z", "audit_at": CUTOFF}
SNAPSHOT = {"user_id": "custom_subject", "email": "person@example.org", "phone": "", "email_hash": "", "name": "Fixture"}
RULES = [{"data_category": "USER_PROFILE", "required_action": "DELETE"},
         {"data_category": "SECURITY_AUDIT_LOG", "required_action": "RETAIN"}]
RETAINED = Observation("security_service", "audit_custom", "SECURITY_AUDIT_LOG", "PRESENT", "source_retained",
                       BEFORE, BEFORE, {"custom_subject"}, {"subject_reference": "custom_subject"})
MANIFEST = [{"file_id": "source_retained", "file_path": "evidence/retained.json", "captured_at": BEFORE}]


class InvestigationTests(unittest.TestCase):
    def run_diagnosis(self, store, raw=()):
        return diagnose([REQUEST], store, IdentityIndex([SNAPSHOT], []), [], RULES,
                        {"custom_request": True}, MANIFEST, raw)

    def test_scope_negative_is_not_turned_into_invented_resource_or_verdict(self):
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "customer_profiles", "resources": set(),
                 "complete": True, "evidence_id": "source_snapshot", "captured_at": BEFORE, "observed_at": BEFORE}
        result = self.run_diagnosis(EvidenceStore([RETAINED], [scope]))
        self.assertEqual(result["group_counts"], {"negative_scope_without_owned_resource": 1})
        self.assertEqual(result["resolved_count"], 0)
        case = result["cases"][0]
        self.assertEqual(case["account_observations"], [])
        self.assertNotIn("steps_json", case)
        self.assertEqual(case["post_request_primary_scope_count"], 1)

    def test_late_capture_stays_distinct_from_late_observation(self):
        profile = Observation("account_service", "account_exact", "USER_PROFILE", "ABSENT", "source_late",
                              AFTER, BEFORE, {"person@example.org"}, {})
        result = self.run_diagnosis(EvidenceStore([RETAINED, profile]))
        case = result["cases"][0]
        self.assertEqual(case["group"], "primary_evidence_after_cutoff")
        self.assertEqual(case["primary_capture_after_cutoff_count"], 1)
        self.assertEqual(case["primary_observation_after_cutoff_count"], 0)
        self.assertEqual(case["account_observations"][0]["resource_id"], "account_exact")

    def test_historical_email_links_primary_evidence_without_using_future_history(self):
        snapshot = {**SNAPSHOT, "email": "new@example.org"}
        changes = [{"user_id": "custom_subject", "field_name": "email", "old_value": "person@example.org",
                    "new_value": "new@example.org", "event_time": BEFORE},
                   {"user_id": "custom_subject", "field_name": "phone", "old_value": "+1 555 000 0001",
                    "new_value": "+1 555 000 0002", "event_time": AFTER}]
        profile = Observation("account_service", "account_exact", "USER_PROFILE", "ABSENT", "source_late",
                              AFTER, BEFORE, {"person@example.org"}, {})
        result = diagnose([REQUEST], EvidenceStore([RETAINED, profile]), IdentityIndex([snapshot], changes), changes,
                          RULES, {"custom_request": True}, MANIFEST)
        case = result["cases"][0]
        self.assertEqual(case["group"], "primary_evidence_after_cutoff")
        self.assertEqual(case["missing_past_identifier_count"], 0)
        self.assertEqual(case["historical_identifier_count"], 2)

    def test_eligible_raw_record_becomes_parser_lead_not_prediction(self):
        raw = {"resource_id": "account_exact", "category": "USER_PROFILE", "evidence_id": "source_raw",
               "source_path": "evidence/raw.json", "locator": "$.records[0]", "captured_at": BEFORE,
               "observed_at": BEFORE, "identifiers": {"person@example.org"}}
        result = self.run_diagnosis(EvidenceStore([RETAINED]), [raw])
        self.assertEqual(result["group_counts"], {"raw_primary_record_not_parsed": 1})
        self.assertEqual(result["resolved_count"], 0)
        self.assertEqual(result["checks"]["raw_primary_parser_review_cases"], 1)

    def test_missing_primary_evidence_is_reported_and_markdown_has_exact_sources(self):
        result = self.run_diagnosis(EvidenceStore([RETAINED]))
        self.assertEqual(result["group_counts"], {"no_primary_evidence_or_scope": 1})
        text = markdown(result)
        self.assertIn("No eligible direct account/tombstone row", text)
        self.assertIn("custom_request", text)
        self.assertNotIn("person@example.org", text)

    def test_reviewed_partial_identifier_view_has_its_own_evidence_uncertainty_group(self):
        reviewed = Observation("identity_service", "tombstone_exact", "ACCOUNT_TOMBSTONE", "UNKNOWN", "source_review",
                               BEFORE, BEFORE, {"custom_subject"},
                               {"_media": True, "_media_reinspection": True,
                                "_uncertainty": "Email hash was not shown; partial field coverage is not redaction proof."})
        result = self.run_diagnosis(EvidenceStore([RETAINED, reviewed]))
        self.assertEqual(result["group_counts"], {"media_field_coverage_uncertainty": 1})
        source = result["cases"][0]["media_uncertainties"][0]
        self.assertIn("Email hash was not shown", source["uncertainty"])
        self.assertIn("partial field coverage", markdown(result))

    def test_raw_entity_scan_does_not_join_neighboring_json_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = Path(folder)
            (dataset / "records.json").write_text(json.dumps({"records": [
                {"resource_id": "account_exact", "email": "other@example.org"},
                {"resource_id": "support_exact", "requester_email": "person@example.org"}]}), encoding="utf-8")
            result = raw_primary_records(dataset, [{"file_id": "raw", "file_path": "records.json", "captured_at": BEFORE}])
            self.assertEqual(len(result), 1)
            self.assertNotIn("person@example.org", result[0]["identifiers"])
            self.assertEqual(result[0]["locator"], "$.records[0]")

    def test_raw_sql_scan_respects_declared_scope_observation_time(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = Path(folder)
            sql = ("CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);"
                   f"INSERT INTO snapshot_scope VALUES('account_service','{AFTER}');"
                   "CREATE TABLE customer_profiles(resource_id TEXT,email TEXT);"
                   "INSERT INTO customer_profiles VALUES('account_exact','person@example.org');")
            (dataset / "records.sql").write_text(sql, encoding="utf-8")
            records = raw_primary_records(dataset, [{"file_id": "raw", "file_path": "records.sql", "captured_at": BEFORE}])
            self.assertEqual(records[0]["observed_at"], AFTER)
            result = self.run_diagnosis(EvidenceStore([RETAINED]), records)
            self.assertNotEqual(result["cases"][0]["group"], "raw_primary_record_not_parsed")

    def test_raw_trace_scan_retains_lookup_context_without_resource_guessing(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = Path(folder)
            text = (f'{BEFORE} service=account_service trace_id=custom event=lookup_started lookup_key="person@example.org"\n'
                    f'{BEFORE} service=account_service trace_id=custom event=lookup_completed resource_id=account_exact rows=0\n')
            (dataset / "events.log").write_text(text, encoding="utf-8")
            result = raw_primary_records(dataset, [{"file_id": "raw", "file_path": "events.log", "captured_at": BEFORE}])
            self.assertEqual(len(result), 1)
            self.assertIn("person@example.org", result[0]["identifiers"])
            self.assertEqual(result[0]["resource_id"], "account_exact")
            self.assertEqual(result[0]["locator"], "line 2")

    def test_negative_lookup_without_resource_id_is_a_diagnostic_not_guessed_id(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = Path(folder)
            text = (f'{BEFORE} service=account_service trace_id=custom event=profile_lookup_started lookup_key="person@example.org"\n'
                    f'{BEFORE} service=account_service trace_id=custom event=profile_lookup_completed rows=0 http_status=404\n')
            (dataset / "events.log").write_text(text, encoding="utf-8")
            raw = raw_primary_records(dataset, [{"file_id": "raw", "file_path": "events.log", "captured_at": BEFORE}])
            self.assertEqual(len(raw), 1)
            self.assertEqual(raw[0]["resource_id"], "")
            result = self.run_diagnosis(EvidenceStore([RETAINED]), raw)
            self.assertEqual(result["group_counts"], {"primary_query_without_resource_id": 1})
            self.assertEqual(result["resolved_count"], 0)

    def test_report_cli_rejects_writing_participant_data_before_loading_caches(self):
        module = importlib.import_module("investigate")
        with patch.object(module, "load_context") as load:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                module.main(["--report", str(module.ROOT / "dataset/new_report.md")])
        self.assertEqual(caught.exception.code, 2)
        load.assert_not_called()

    def test_reinspection_loader_is_offline_and_joins_catalog_only_after_extraction(self):
        module = importlib.import_module("investigate")
        first = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE, "details": "Literal alias (business.pdf)",
                 "resource_id": "object_exact", "target_system": "object_storage", "activity_id": "catalog_first"}
        second = {**first, "activity_id": "catalog_second", "resource_id": "object_other"}
        store = EvidenceStore(activities=[first, {"event_type": "UNRELATED_EVENT"}, second])
        path, meta = Path("business.pdf"), {"file_id": "media", "captured_at": BEFORE}
        store.media = [(path, meta)]
        with patch.object(module, "load_evidence", return_value=store), \
             patch.object(module, "read_csv", return_value=[]), \
             patch.object(module, "GeminiClient") as client_type, \
             patch.object(module, "extract_media", return_value={"records": [{}]}), \
             patch.object(module, "hydrate_media"), \
             patch.object(module, "reinspect_media", return_value={"records": []}) as review, \
             patch.object(module, "hydrate_media_reinspection") as hydrate:
            module.load_context(Path("root"), Path("dataset"), reinspect=True)
        client_type.assert_called_once_with(Path("root"), offline=True)
        review.assert_called_once_with(client_type.return_value, path, meta, [])
        hydrate.assert_called_once_with(store, meta, {"records": []}, [first, second])


if __name__ == "__main__":
    unittest.main()
