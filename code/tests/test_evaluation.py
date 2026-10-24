import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import serialize_steps

_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "main.py"
_SPEC = importlib.util.spec_from_file_location("audit_evaluator", _PATH)
evaluator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(evaluator)


def row(case_id="example", steps=None, status="COMPLETE"):
    if steps is None:
        steps = [{"phase": "VERIFICATION", "system_id": "accounts", "resource_id": "resource_a",
                  "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_a"}]
        steps = serialize_steps(steps)
    return {"case_id": case_id, "deletion_status": status, "steps_json": json.dumps(steps)}


class EvaluationTests(unittest.TestCase):
    def write_output(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=evaluator.COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def invoke(self, predictions, expected, report, *additional):
        return subprocess.run([sys.executable, str(_PATH), "--predictions", str(predictions),
                               "--expected", str(expected), "--report", str(report), *map(str, additional)],
                              capture_output=True, text=True)

    def test_exact_match_and_json_object_order_do_not_change_metrics(self):
        expected = row()
        steps = json.loads(expected["steps_json"])
        actual = dict(expected, steps_json=json.dumps([dict(reversed(list(steps[0].items())))]))
        metrics = evaluator.evaluate([actual], [expected])
        self.assertTrue(metrics["contract_valid"])
        for name in ("status_accuracy", "exact_case_accuracy", "sequence_accuracy", "step_f1", "field_accuracy"):
            self.assertEqual(metrics[name], 1.0)

    def test_missing_and_extra_case_are_not_silently_ignored(self):
        metrics = evaluator.evaluate([row("a"), row("c")], [row("a"), row("b")])
        self.assertFalse(metrics["contract_valid"])
        self.assertEqual(metrics["missing_case_ids"], ["b"])
        self.assertEqual(metrics["extra_case_ids"], ["c"])
        self.assertAlmostEqual(metrics["status_accuracy"], 1 / 2)
        self.assertEqual(metrics["covered_cases"], 1)
        self.assertEqual(metrics["coverage_rate"], 1 / 2)
        self.assertEqual(metrics["extra_cases"], 1)
        self.assertEqual(metrics["matching_steps"], 1)
        self.assertEqual(metrics["field_accuracy"], 1 / 3)

    def test_full_coverage_does_not_imply_status_or_sequence_accuracy(self):
        expected = [row("a"), row("b")]
        actual = [row("a"), row("b", steps=[], status="NOT_APPLICABLE")]
        metrics = evaluator.evaluate(actual, expected)
        self.assertEqual(metrics["coverage_rate"], 1)
        self.assertTrue(metrics["coverage_complete"])
        self.assertEqual(metrics["status_accuracy"], 1 / 2)
        self.assertEqual(metrics["exact_case_accuracy"], 1 / 2)
        self.assertEqual(metrics["sequence_accuracy"], 1 / 2)

    def test_missing_request_does_not_disappear_from_primary_accuracy(self):
        expected = [row("a"), row("b"), row("c")]
        actual = [row("a"), row("b", steps=[], status="NOT_APPLICABLE")]
        metrics = evaluator.evaluate(actual, expected)
        self.assertEqual(metrics["coverage_rate"], 2 / 3)
        self.assertEqual(metrics["status_accuracy"], 1 / 3)
        self.assertEqual(metrics["returned_case_status_accuracy"], 1 / 2)
        self.assertEqual(metrics["exact_case_correct"], 1)
        self.assertEqual(metrics["scored_cases"], 3)

    def test_extra_case_is_coverage_error_and_step_false_positive(self):
        metrics = evaluator.evaluate([row("a"), row("b"), row("extra")], [row("a"), row("b")])
        self.assertEqual(metrics["coverage_rate"], 1)
        self.assertFalse(metrics["coverage_complete"])
        self.assertEqual(metrics["status_accuracy"], 1)
        self.assertEqual(metrics["returned_case_status_accuracy"], 2 / 3)
        self.assertEqual(metrics["step_precision"], 2 / 3)
        self.assertEqual(metrics["step_recall"], 1)

    def test_missing_step_penalizes_every_field_and_expected_step_recall(self):
        one = json.loads(row()["steps_json"])[0]
        two = dict(one, step_no=2, resource_id="resource_b")
        metrics = evaluator.evaluate([row(steps=[one])], [row(steps=[one, two])])
        self.assertEqual(metrics["coverage_rate"], 1)
        self.assertEqual(metrics["status_accuracy"], 1)
        self.assertEqual(metrics["sequence_accuracy"], 0)
        self.assertEqual(metrics["step_precision"], 1)
        self.assertEqual(metrics["step_recall"], 1 / 2)
        self.assertEqual(metrics["aligned_step_slots"], 2)
        self.assertEqual(metrics["field_accuracy"], 1 / 2)
        self.assertTrue(all(value == 1 / 2 for value in metrics["field_accuracy_by_name"].values()))

    def test_missing_non_deletion_case_is_incorrect_even_without_steps(self):
        metrics = evaluator.evaluate([], [row("a", steps=[], status="NOT_APPLICABLE")])
        self.assertEqual(metrics["coverage_rate"], 0)
        self.assertEqual(metrics["status_accuracy"], 0)
        self.assertEqual(metrics["sequence_accuracy"], 0)
        self.assertEqual(metrics["returned_case_status_accuracy"], 0)

    def test_wrong_citation_is_a_content_error_with_field_alignment(self):
        expected = row()
        steps = json.loads(expected["steps_json"])
        steps[0]["evidence_id"] = "wrong_evidence"
        metrics = evaluator.evaluate([row(steps=steps)], [expected])
        self.assertEqual(metrics["status_accuracy"], 1)
        self.assertEqual(metrics["step_f1"], 0)
        self.assertEqual(metrics["field_accuracy_by_name"]["evidence_id"], 0)
        self.assertEqual(metrics["field_accuracy"], 6 / 7)

    def test_order_error_keeps_content_score_and_fails_sequence(self):
        steps = json.loads(row()["steps_json"])
        second = dict(steps[0], resource_id="resource_b", step_no=2)
        expected = row(steps=steps + [second])
        reordered = [dict(second, step_no=1), dict(steps[0], step_no=2)]
        metrics = evaluator.evaluate([row(steps=reordered)], [expected])
        self.assertEqual(metrics["step_f1"], 1)
        self.assertEqual(metrics["sequence_accuracy"], 0)
        self.assertFalse(metrics["contract_valid"])

    def test_duplicate_ids_and_malformed_steps_fail(self):
        with self.assertRaisesRegex(ValueError, "duplicate case ID"):
            evaluator.evaluate([row(), row()], [row()])
        with self.assertRaisesRegex(ValueError, "array"):
            evaluator.evaluate([dict(row(), steps_json="{}")], [row()])
        with self.assertRaisesRegex(ValueError, "zero-case"):
            evaluator.evaluate([], [])

    def test_missing_predictions_cannot_overwrite_existing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            report = directory / "existing.md"
            report.write_text("Previous measured result", encoding="utf-8")
            result = subprocess.run([sys.executable, str(_PATH), "--predictions", str(directory / "missing.csv"),
                                     "--report", str(report)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(report.read_text(encoding="utf-8"), "Previous measured result")

    def test_report_cannot_overwrite_a_participant_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            dataset = directory / "dataset"
            dataset.mkdir()
            predictions, expected = directory / "predictions.csv", dataset / "sample_output.csv"
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            participant_input = dataset / "deletion_requests.csv"
            participant_input.write_bytes(b"Original participant input\n")
            result = self.invoke(predictions, expected, participant_input)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(participant_input.read_bytes(), b"Original participant input\n")

    def test_json_input_collision_is_rejected_before_report_write(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            predictions, expected, report = (directory / name for name in ("predictions.csv", "expected.csv", "report.md"))
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            original = predictions.read_bytes()
            report.write_bytes(b"Previous report remains valid\n")
            result = self.invoke(predictions, expected, report, "--json", predictions)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(predictions.read_bytes(), original)
            self.assertEqual(report.read_bytes(), b"Previous report remains valid\n")

    def test_custom_dataset_blocks_new_markdown_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            dataset = directory / "participant_inputs"
            dataset.mkdir()
            predictions, expected = directory / "predictions.csv", dataset / "sample_output.csv"
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            (dataset / "sample_deletion_requests.csv").write_text("Participant input marker\n", encoding="utf-8")
            report = dataset / "new_report.md"
            result = self.invoke(predictions, expected, report)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(report.exists())

    def test_repository_readme_cannot_be_overwritten_as_a_report(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            predictions, expected = directory / "predictions.csv", directory / "expected.csv"
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            source = evaluator.ROOT / "README.md"
            original = source.read_bytes()
            result = self.invoke(predictions, expected, source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), original)

    def test_external_python_source_cannot_be_overwritten_as_a_report(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            predictions, expected, source = (directory / name for name in ("predictions.csv", "expected.csv", "helper.py"))
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            source.write_bytes(b"print('Preserve this program')\n")
            result = self.invoke(predictions, expected, source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), b"print('Preserve this program')\n")

    def test_explicit_external_report_and_json_destinations_work(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            predictions, expected = directory / "predictions.csv", directory / "expected.csv"
            report, metrics_path = directory / "report.md", directory / "metrics.json"
            self.write_output(predictions, [row()])
            self.write_output(expected, [row()])
            original_predictions, original_expected = predictions.read_bytes(), expected.read_bytes()
            result = self.invoke(predictions, expected, report, "--json", metrics_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(report.read_text(encoding="utf-8").startswith("# Public sample evaluation"))
            self.assertEqual(json.loads(metrics_path.read_text(encoding="utf-8"))["exact_case_accuracy"], 1)
            self.assertEqual(predictions.read_bytes(), original_predictions)
            self.assertEqual(expected.read_bytes(), original_expected)


if __name__ == "__main__":
    unittest.main()
