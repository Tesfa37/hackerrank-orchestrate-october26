"""CLI integration regressions using synthetic input and no network/model calls."""
import argparse
import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import Observation, read_csv, validate_citations, validate_output
from evidence import EvidenceStore

_PATH = Path(__file__).resolve().parents[1] / "main.py"
_SPEC = importlib.util.spec_from_file_location("audit_cli", _PATH)
cli = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cli)


class MainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dataset = self.root / "dataset"
        self.dataset.mkdir()
        self.request = {"case_id": "example_a", "email": "person@example.test",
                        "requested_at": "2026-09-01T00:00:00Z", "reported_status": "COMPLETE",
                        "reported_at": "2026-09-02T00:00:00Z", "audit_at": "2026-09-10T12:00:00Z",
                        "request_text": "Please erase my account."}
        for filename in ("deletion_requests.csv", "sample_deletion_requests.csv"):
            self.write_csv(filename, list(self.request), [self.request])
        self.write_csv("user_identities.csv", ["user_id", "email", "name", "phone", "email_hash"],
                       [{"user_id": "person_a", "email": self.request["email"], "name": "Example Person",
                         "phone": "", "email_hash": ""}])
        self.write_csv("user_audit_log.csv", ["audit_id", "user_id", "field_name", "old_value", "new_value", "event_time"], [])
        self.write_csv("deletion_rules.csv", ["data_category", "required_action"],
                       [{"data_category": "USER_PROFILE", "required_action": "DELETE"}])
        self.meta = {"file_id": "evidence_a", "file_path": "evidence.json", "origin": "account_service",
                     "captured_at": "2026-09-09T12:00:00Z"}
        self.write_csv("evidence_files.csv", list(self.meta), [self.meta])
        self.write_csv("system_activity.csv", ["activity_id", "event_time", "target_system", "resource_id", "details"], [])
        self.observation = Observation("account_service", "account_example", "USER_PROFILE", "PRESENT",
                                       self.meta["file_id"], self.meta["captured_at"], self.meta["captured_at"],
                                       {self.request["email"], "person_a"})
        self.store = EvidenceStore(observations=[self.observation])
        self.addCleanup(patch.stopall)
        patch.object(cli, "ROOT", self.root).start()
        patch.object(cli, "load_evidence", return_value=self.store).start()
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def write_csv(self, name, fields, rows):
        with (self.dataset / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def args(self, **changes):
        values = dict(dataset=self.dataset, samples=False, case=None, output=None,
                      partial=False, prepare=False, offline=True, usage_report=None)
        values.update(changes)
        return argparse.Namespace(**values)

    def run_cli(self, **changes):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            return cli.run(self.args(**changes))

    def preserve_existing_output(self):
        output = self.root / "output.csv"
        output.write_text("Previously validated output\n", encoding="utf-8")
        return output

    def test_prepare_writes_jobs_but_never_predictions(self):
        output = self.preserve_existing_output()
        media = self.dataset / "screen.png"
        media.write_bytes(b"synthetic queued image")
        self.store.media.append((media, dict(self.meta, file_id="media_a")))
        self.assertEqual(self.run_cli(prepare=True, offline=False), 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")
        jobs = json.loads((self.root / ".cache" / "model_jobs.json").read_text(encoding="utf-8"))
        self.assertEqual({job["task"] for job in jobs}, {"request-intent", "business-artifact-extraction"})
        self.assertFalse((self.root / "sample_predictions.csv").exists())

    def test_missing_offline_intent_preserves_existing_output(self):
        output = self.preserve_existing_output()
        self.assertEqual(self.run_cli(), 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")
        ledger = json.loads((self.root / ".cache" / "run_full.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["completed"], 0)
        self.assertTrue(any(error["stage"] == "intent" for error in ledger["errors"]))

    def test_missing_offline_media_cannot_become_a_deletion_verdict(self):
        output = self.preserve_existing_output()
        media = self.dataset / "screen.png"
        media.write_bytes(b"synthetic missing extraction")
        self.store.media.append((media, dict(self.meta, file_id="media_a")))
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: True}):
            self.assertEqual(self.run_cli(), 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")
        self.assertEqual(self.store.hydrated_media, set())

    def test_missing_semantic_review_cannot_reuse_flat_media_as_proof(self):
        output = self.preserve_existing_output()
        media = self.dataset / "screen.png"
        media.write_bytes(b"synthetic flat-only extraction")
        self.store.media.append((media, dict(self.meta, file_id="media_a")))
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: True}), \
             patch.object(cli, "extract_media", return_value={"records": []}):
            self.assertEqual(self.run_cli(reinspect_media=True), 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")
        self.assertEqual(self.store.hydrated_media, {"media_a"})
        self.assertEqual(self.store.reinspected_media, set())

    def test_preparation_keeps_unprinted_catalog_ids_out_of_model_review(self):
        output = self.preserve_existing_output()
        self.store.activities.append({"activity_id": "catalog_a", "event_type": "LINK_RESOURCE_IDENTITY",
                                      "event_time": self.meta["captured_at"], "target_system": "account_service",
                                      "resource_id": "account_unprinted", "details": "Linked account_unprinted (literal) to person_a"})
        media = self.dataset / "screen.png"
        media.write_bytes(b"synthetic source-only review")
        self.store.media.append((media, dict(self.meta, file_id="media_a")))
        self.assertEqual(self.run_cli(prepare=True, offline=False, reinspect_media=True), 0)
        jobs = json.loads((self.root / ".cache" / "model_jobs.json").read_text(encoding="utf-8"))
        review = next(job for job in jobs if job["task"] == "business-artifact-semantic-reinspection-v1")
        self.assertNotIn("account_unprinted", json.dumps(review["body"]))
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")

    def test_partial_output_requires_explicit_development_destination(self):
        output = self.preserve_existing_output()
        with self.assertRaisesRegex(ValueError, "explicit"):
            self.run_cli(partial=True)
        with self.assertRaisesRegex(ValueError, "final root"):
            self.run_cli(partial=True, output=output)
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")

    def test_non_deletion_short_circuit_never_resolves_identity(self):
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: False}), \
             patch.object(cli.IdentityIndex, "resolve", side_effect=AssertionError("Identity resolution is unauthorized")):
            self.assertEqual(self.run_cli(), 0)
        rows = read_csv(self.root / "output.csv")
        self.assertEqual(rows, [{"case_id": self.request["case_id"], "deletion_status": "NOT_APPLICABLE", "steps_json": "[]"}])

    def test_output_cannot_overwrite_participant_dataset(self):
        original = (self.dataset / "deletion_requests.csv").read_bytes()
        with self.assertRaisesRegex(ValueError, "participant input"):
            self.run_cli(output=self.dataset / "deletion_requests.csv")
        self.assertEqual((self.dataset / "deletion_requests.csv").read_bytes(), original)

    def test_usage_report_cannot_overwrite_participant_dataset(self):
        original = (self.dataset / "deletion_requests.csv").read_bytes()
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: False}):
            with self.assertRaisesRegex(ValueError, "participant input|dataset"):
                self.run_cli(usage_report=self.dataset / "deletion_requests.csv")
        self.assertEqual((self.dataset / "deletion_requests.csv").read_bytes(), original)

    def test_case_selection_cannot_replace_the_final_full_output(self):
        other = dict(self.request, case_id="example_b")
        self.write_csv("deletion_requests.csv", list(self.request), [self.request, other])
        output = self.preserve_existing_output()
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: False}):
            with self.assertRaisesRegex(ValueError, "case|development|subset|output"):
                self.run_cli(case=[self.request["case_id"]])
        self.assertEqual(output.read_text(encoding="utf-8"), "Previously validated output\n")

    def test_successful_synthetic_audit_writes_strict_csv_with_grounded_citations(self):
        with patch.object(cli, "classify_requests", return_value={self.request["case_id"]: True}):
            self.assertEqual(self.run_cli(), 0)
        output = self.root / "output.csv"
        self.assertEqual(output.read_text(encoding="utf-8").splitlines()[0], "case_id,deletion_status,steps_json")
        rows = read_csv(output)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["deletion_status"], "INCOMPLETE")
        steps = json.loads(rows[0]["steps_json"])
        self.assertEqual([step["operation"] for step in steps],
                         ["REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"])
        self.assertEqual([step["evidence_id"] for step in steps], ["evidence_a", "", ""])
        validate_output(rows, [self.request])
        validate_citations(rows, [self.request], [self.meta], observations=[self.observation])
        self.assertFalse(output.with_name(output.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
