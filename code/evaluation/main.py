"""Evaluate public development predictions without importing prediction logic.

Expected answers are consumed only by this evaluator. Missing or extra cases are
measured as failures rather than silently dropped by an inner join.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import STEP_FIELDS, validate_output


ROOT = Path(__file__).resolve().parents[2]
COLUMNS = ["case_id", "deletion_status", "steps_json"]
FIELDS = ("step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id")
ALIGN_FIELDS = ("phase", "system_id", "resource_id", "operation")
CONTENT_FIELDS = tuple(field for field in FIELDS if field != "step_no")


def load_predictions(path: Path) -> list[dict]:
    """Read either predictions or expected output with the exact CSV header."""
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path}: CSV header must be {','.join(COLUMNS)}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path}: CSV rows must contain exactly three values")
    return rows


def _index(rows: list[dict], label: str) -> tuple[dict, list[dict]]:
    indexed, errors = {}, []
    for row in rows:
        if set(row) != set(COLUMNS):
            raise ValueError(f"{label}: output columns differ from the contract")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{label}: case IDs must be nonempty strings")
        if case_id in indexed:
            raise ValueError(f"{label}: duplicate case ID {case_id}")
        try:
            steps = json.loads(row["steps_json"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"{label}: {case_id}: steps_json is not valid JSON") from exc
        if not isinstance(steps, list):
            raise ValueError(f"{label}: {case_id}: steps_json must be an array")
        for step in steps:
            if not isinstance(step, dict) or set(step) != STEP_FIELDS:
                raise ValueError(f"{label}: {case_id}: steps require exactly seven contract fields")
            if type(step["step_no"]) is not int:
                raise ValueError(f"{label}: {case_id}: step_no must be an integer")
            if any(not isinstance(step[field], str) for field in CONTENT_FIELDS):
                raise ValueError(f"{label}: {case_id}: step values must be strings")
        try:
            validate_output([row], [{"case_id": case_id}])
        except (ValueError, TypeError, KeyError) as exc:
            errors.append({"case_id": case_id, "error": str(exc)})
        indexed[case_id] = {"status": row["deletion_status"], "steps": steps}
    if [row["case_id"] for row in rows] != sorted(indexed):
        errors.append({"case_id": "", "error": "CSV rows are not sorted by case_id"})
    return indexed, errors


def _aligned_steps(predicted: list[dict], expected: list[dict]):
    """Align exact resource/operation keys; preserve unmatched slots as errors.

    Duplicate keys are matched by exact step equality first, then input order.
    They normally indicate a contract violation, but still receive finite scores.
    """
    predicted_groups, expected_groups = defaultdict(list), defaultdict(list)
    for step in predicted:
        predicted_groups[tuple(step[field] for field in ALIGN_FIELDS)].append(step)
    for step in expected:
        expected_groups[tuple(step[field] for field in ALIGN_FIELDS)].append(step)
    for key in sorted(predicted_groups.keys() | expected_groups.keys()):
        left, right = list(predicted_groups[key]), list(expected_groups[key])
        unmatched = []
        for step in left:
            if step in right:
                right.remove(step)
                yield step, step
            else:
                unmatched.append(step)
        for number in range(max(len(unmatched), len(right))):
            yield (unmatched[number] if number < len(unmatched) else None,
                   right[number] if number < len(right) else None)


def _fraction(numerator: int, denominator: int, empty: float = 0.0) -> float:
    return numerator / denominator if denominator else empty


def evaluate(predictions: list[dict], expected: list[dict]) -> dict:
    """Return measured metrics and bounded mismatch summaries.

    Primary case accuracy always uses every expected request. Missing cases are
    incorrect; extra IDs are separately reported as coverage/contract failures
    and their steps count as false positives. Step matching compares the six
    content fields; sequence accuracy checks array order and numbering too.
    """
    pred, contract_errors = _index(predictions, "Predictions")
    gold, expected_errors = _index(expected, "Expected output")
    if not gold:
        raise ValueError("Expected output is empty; a zero-case run cannot establish accuracy")
    if expected_errors:
        raise ValueError(f"Expected output violates the contract: {expected_errors[0]}")
    ids = sorted(pred.keys() | gold.keys())
    missing, extra = sorted(gold.keys() - pred.keys()), sorted(pred.keys() - gold.keys())
    status_correct = sequence_correct = exact_correct = matched_steps = 0
    predicted_steps = expected_steps = aligned_slots = 0
    field_correct = Counter({field: 0 for field in FIELDS})
    mismatches = []
    for case_id in ids:
        actual, answer = pred.get(case_id), gold.get(case_id)
        actual_steps = actual["steps"] if actual else []
        answer_steps = answer["steps"] if answer else []
        has_both = actual is not None and answer is not None
        status_match = has_both and actual["status"] == answer["status"]
        sequence_match = has_both and actual_steps == answer_steps
        status_correct += bool(status_match)
        sequence_correct += bool(sequence_match)
        exact_correct += bool(status_match and sequence_match)
        actual_counter = Counter(tuple(step[field] for field in CONTENT_FIELDS) for step in actual_steps)
        answer_counter = Counter(tuple(step[field] for field in CONTENT_FIELDS) for step in answer_steps)
        common = sum((actual_counter & answer_counter).values())
        matched_steps += common
        predicted_steps += len(actual_steps)
        expected_steps += len(answer_steps)
        for left, right in _aligned_steps(actual_steps, answer_steps):
            aligned_slots += 1
            if left is not None and right is not None:
                for field in FIELDS:
                    field_correct[field] += left[field] == right[field]
        if not (status_match and sequence_match):
            mismatches.append({
                "case_id": case_id,
                "expected_status": answer["status"] if answer else None,
                "predicted_status": actual["status"] if actual else None,
                "expected_steps": len(answer_steps),
                "predicted_steps": len(actual_steps),
                "matching_steps": common,
                "status_match": bool(status_match),
                "sequence_match": bool(sequence_match),
            })
    precision = _fraction(matched_steps, predicted_steps, 1.0 if not expected_steps else 0.0)
    recall = _fraction(matched_steps, expected_steps, 1.0 if not predicted_steps else 0.0)
    return {
        "expected_cases": len(gold), "predicted_cases": len(pred), "scored_cases": len(gold),
        "case_id_union": len(ids), "covered_cases": len(gold.keys() & pred.keys()),
        "coverage_rate": _fraction(len(gold.keys() & pred.keys()), len(gold)),
        "missing_cases": len(missing), "extra_cases": len(extra),
        "missing_case_ids": missing, "extra_case_ids": extra,
        "coverage_complete": not missing and not extra,
        "contract_valid": not contract_errors and not missing and not extra,
        "contract_errors": contract_errors,
        "status_correct": status_correct,
        "status_accuracy": _fraction(status_correct, len(gold)),
        "expected_case_status_accuracy": _fraction(status_correct, len(gold)),
        "returned_case_status_accuracy": _fraction(status_correct, len(pred)),
        "exact_case_correct": exact_correct,
        "exact_case_accuracy": _fraction(exact_correct, len(gold)),
        "sequence_correct": sequence_correct,
        "sequence_accuracy": _fraction(sequence_correct, len(gold)),
        "expected_steps": expected_steps, "predicted_steps": predicted_steps,
        "matching_steps": matched_steps, "step_precision": precision, "step_recall": recall,
        "step_f1": _fraction(2 * precision * recall, precision + recall),
        "aligned_step_slots": aligned_slots,
        "field_accuracy": _fraction(sum(field_correct.values()), aligned_slots * len(FIELDS), 1.0),
        "field_accuracy_by_name": {field: _fraction(field_correct[field], aligned_slots, 1.0) for field in FIELDS},
        "field_correct_by_name": dict(field_correct),
        "mismatches": mismatches,
    }


def render_report(metrics: dict, predictions: Path, expected: Path) -> str:
    """Render results without asserting that development accuracy is hidden accuracy."""
    lines = [
        "# Public sample evaluation", "",
        f"Generated {datetime.now(timezone.utc).isoformat()} from `{predictions.name}` against `{expected.name}`.", "",
        "The public examples are development data. These measurements do not establish hidden evaluation accuracy.", "",
        "## Prediction coverage", "",
        "Coverage records which requests received a row; it is separate from agreement with expected answers.", "",
        "| Coverage measure | Result |", "| --- | ---: |",
        f"| Expected / returned cases | {metrics['expected_cases']} / {metrics['predicted_cases']} |",
        f"| Expected cases with a prediction | {metrics['covered_cases']}/{metrics['expected_cases']} ({metrics['coverage_rate']:.2%}) |",
        f"| Missing / unexpected case IDs | {metrics['missing_cases']} / {metrics['extra_cases']} |",
        f"| Exact case-ID coverage | {'Pass' if metrics['coverage_complete'] else 'Fail'} |",
        f"| Output contract | {'Pass' if metrics['contract_valid'] else 'Fail'} |",
        "", "## Accuracy across every expected request", "",
        "All expected requests remain in the primary case-accuracy denominators. A missing prediction is incorrect.", "",
        "| Accuracy measure | Result |", "| --- | ---: |",
        f"| Deletion-status accuracy | {metrics['status_accuracy']:.2%} ({metrics['status_correct']}/{metrics['expected_cases']}) |",
        f"| Exact case accuracy (status and ordered steps) | {metrics['exact_case_accuracy']:.2%} ({metrics['exact_case_correct']}/{metrics['expected_cases']}) |",
        f"| Exact step-sequence accuracy | {metrics['sequence_accuracy']:.2%} ({metrics['sequence_correct']}/{metrics['expected_cases']}) |",
        f"| Step precision / recall / F1 | {metrics['step_precision']:.2%} / {metrics['step_recall']:.2%} / {metrics['step_f1']:.2%} |",
        f"| Exact content-matched / predicted / expected steps | {metrics['matching_steps']} / {metrics['predicted_steps']} / {metrics['expected_steps']} |",
        f"| Aligned field accuracy | {metrics['field_accuracy']:.2%} |", "",
        f"Supplementary returned-row status agreement is {metrics['status_correct']}/{metrics['predicted_cases']} "
        f"({metrics['returned_case_status_accuracy']:.2%}). It excludes missing expected rows and must not replace the primary all-request accuracy.", "",
        "## Metric definitions", "",
        "Primary case metrics divide by every expected request; missing rows count as incorrect. "
        "Unexpected IDs fail coverage/contract checks and their steps count as false positives. "
        "Exact sequence compares the entire ordered step array, including numbering, but scores status separately. "
        "Step precision/recall/F1 compare multisets of the six content fields, excluding `step_no`; "
        "citations count as content, and recall includes expected steps from every missing request. "
        "Fields align by `(phase, system_id, resource_id, operation)`. "
        "For duplicate keys, exact steps align first and remaining steps align in input order. "
        "Every missing or extra aligned slot is incorrect for all seven fields. "
        "Field accuracy divides correct fields by seven times the aligned slot count. "
        "Empty-versus-empty step metrics equal 100%, while primary case accuracy still penalizes absent rows.", "",
        "| Field | Correct / aligned slots | Accuracy |", "| --- | ---: | ---: |",
    ]
    lines.extend(f"| {field} | {metrics['field_correct_by_name'][field]}/{metrics['aligned_step_slots']} | {metrics['field_accuracy_by_name'][field]:.2%} |" for field in FIELDS)
    lines.extend(["", "## Failures", ""])
    if metrics["missing_case_ids"]:
        lines.append("Missing case IDs: " + ", ".join(metrics["missing_case_ids"]) + ".")
    if metrics["extra_case_ids"]:
        lines.append("Extra case IDs: " + ", ".join(metrics["extra_case_ids"]) + ".")
    for item in metrics["contract_errors"]:
        lines.append(f"- Contract: `{item['case_id']}`: {item['error']}")
    if not metrics["mismatches"]:
        lines.append("No mismatches against the supplied public answers.")
    else:
        lines.extend(["", "| Case | Expected status | Predicted status | Expected steps | Predicted steps | Content matches | Sequence match |",
                      "| --- | --- | --- | ---: | ---: | ---: | --- |"])
        for item in metrics["mismatches"]:
            lines.append(f"| {item['case_id']} | {item['expected_status']} | {item['predicted_status']} | "
                         f"{item['expected_steps']} | {item['predicted_steps']} | {item['matching_steps']} | {item['sequence_match']} |")
    lines.extend(["", "## Independent evaluator regression cases", "",
                  "These fixtures test scoring behavior; reasoning-specific synthetic audits and improvements are documented separately.", "",
                  "1. A missing expected row counts as incorrect in all-request accuracy; an extra prediction separately fails coverage and contributes false-positive steps.",
                  "2. A wrong citation keeps resource alignment but lowers evidence-field accuracy and exact-step precision/recall.",
                  "3. Reordered steps keep content precision/recall but fail sequence accuracy and canonical-order validation.", ""])
    return "\n".join(lines)


def validate_destinations(predictions: Path, expected: Path, report: Path, json_path: Path | None) -> None:
    """Protect inputs and source files before writing either evaluation output.

    Custom datasets are identified from their directory name or participant-file
    markers, rather than assuming that they live below this checkout's root.
    """
    inputs = {predictions.resolve(), expected.resolve()}
    dataset_roots = {(ROOT / "dataset").resolve()}
    markers = ("deletion_requests.csv", "sample_deletion_requests.csv", "evidence_files.csv")
    for source in inputs:
        for parent in source.parents:
            if parent.name.casefold() == "dataset" or any((parent / marker).is_file() for marker in markers):
                dataset_roots.add(parent)
    destinations = [(report, ".md")]
    if json_path is not None:
        destinations.append((json_path, ".json"))
    resolved = []
    root = ROOT.resolve()
    allowed_report = (root / "code" / "evaluation" / "evaluation_report.md").resolve()
    cache = (root / ".cache").resolve()
    for destination, suffix in destinations:
        target = destination.resolve()
        if target in inputs:
            raise ValueError("Evaluation outputs must not overwrite prediction or expected inputs")
        if any(target.is_relative_to(dataset) for dataset in dataset_roots):
            raise ValueError("Evaluation outputs must not overwrite participant datasets")
        if target.suffix.casefold() != suffix:
            raise ValueError(f"Evaluation output requires a {suffix} filename")
        if target.is_relative_to(root) and target != allowed_report and not target.is_relative_to(cache):
            raise ValueError("Evaluation outputs inside the repository are limited to .cache and the evaluation report")
        if target in resolved:
            raise ValueError("Evaluation output destinations must be distinct")
        resolved.append(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, default=ROOT / "sample_predictions.csv")
    parser.add_argument("--expected", type=Path, default=ROOT / "dataset" / "sample_output.csv")
    parser.add_argument("--report", type=Path, default=ROOT / "code" / "evaluation" / "evaluation_report.md")
    parser.add_argument("--json", type=Path, dest="json_path", help="Optional machine-readable metrics destination")
    args = parser.parse_args(argv)
    try:
        validate_destinations(args.predictions, args.expected, args.report, args.json_path)
        metrics = evaluate(load_predictions(args.predictions), load_predictions(args.expected))
        report = render_report(metrics, args.predictions, args.expected)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        if args.json_path:
            args.json_path.parent.mkdir(parents=True, exist_ok=True)
            args.json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Evaluation failed: {exc}\n")
    print(json.dumps({name: metrics[name] for name in (
        "expected_cases", "predicted_cases", "covered_cases", "coverage_rate", "coverage_complete", "contract_valid", "status_accuracy",
        "exact_case_accuracy", "sequence_accuracy", "step_precision", "step_recall", "step_f1", "field_accuracy")}, indent=2))
    return 0 if metrics["contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
