"""Shared input, identity, observation, and exact-output contract primitives."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

OPERATIONS = {
    "FINDING": ["REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"],
    "REMEDIATION": ["DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"],
    "VERIFICATION": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED", "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"],
}
STATES = {
    "REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT", "REPORT_ACTIVE_DATA_FLOW": "ACTIVE", "REPORT_RESTORE_RISK": "ACTIVE",
    "DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED", "DELETE_RECORD": "ABSENT", "REDACT_RECORD": "REDACTED", "ANONYMIZE_RECORD": "ANONYMIZED",
    "VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT", "VERIFY_RECORD_REDACTED": "REDACTED", "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED",
}
STEP_FIELDS = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
IDENTITY_FIELDS = {"user_id", "email", "phone", "email_hash"}
FINDING_REMEDIATIONS = {
    "REPORT_REMAINING_RECORD": {"DELETE_RECORD"},
    "REPORT_EXPOSED_PII": {"REDACT_RECORD", "ANONYMIZE_RECORD"},
    "REPORT_ACTIVE_DATA_FLOW": {"DISABLE_DATA_FLOW"},
    "REPORT_RESTORE_RISK": {"BLOCK_RESTORE"},
}
REMEDIATION_VERIFICATIONS = {
    "DELETE_RECORD": "VERIFY_RECORD_ABSENT",
    "REDACT_RECORD": "VERIFY_RECORD_REDACTED",
    "ANONYMIZE_RECORD": "VERIFY_RECORD_ANONYMIZED",
    "DISABLE_DATA_FLOW": "VERIFY_DATA_FLOW_DISABLED",
    "BLOCK_RESTORE": "VERIFY_RESTORE_BLOCKED",
}


def read_csv(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A nonempty ISO-8601 timestamp is required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamps must include a timezone")
    return result.astimezone(timezone.utc)


def norm(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if "@" in text:
        return text.casefold()
    if re.fullmatch(r"[+()\d .-]+", text) and len(re.sub(r"\D", "", text)) >= 7:
        return re.sub(r"\D", "", text)
    return text


@dataclass
class Subject:
    user_id: str
    identifiers: set[str]
    names: set[str] = field(default_factory=set)


class IdentityIndex:
    def __init__(self, snapshots: list[dict], history: list[dict]):
        self.snapshots = snapshots
        self.history = {}
        for row in history:
            self.history.setdefault(row["user_id"], []).append(row)

    def resolve(self, email: str, cutoff: str) -> Subject:
        matches = []
        limit = timestamp(cutoff)
        for row in self.snapshots:
            history = self.history.get(row["user_id"], [])
            current = dict(row)
            for change in sorted(history, key=lambda item: timestamp(item["event_time"]), reverse=True):
                if timestamp(change["event_time"]) > limit:
                    current[change["field_name"]] = change["old_value"]
            values = {norm(current.get(key)) for key in IDENTITY_FIELDS}
            names = {current.get("name", "")}
            for change in history:
                if timestamp(change["event_time"]) <= limit:
                    if change["field_name"] == "name":
                        names.update([change["old_value"], change["new_value"]])
                    elif change["field_name"] in IDENTITY_FIELDS:
                        values.update([norm(change["old_value"]), norm(change["new_value"])])
            values.discard("")
            if norm(email) in values:
                matches.append(Subject(row["user_id"], values, names - {""}))
        if len(matches) != 1:
            raise ValueError(f"Identity resolution requires exactly one subject; found {len(matches)}")
        return matches[0]


@dataclass
class Observation:
    system: str
    resource: str
    category: str
    state: str
    evidence_id: str
    captured_at: str
    observed_at: str
    identifiers: set[str] = field(default_factory=set)
    data: dict = field(default_factory=dict)
    scope: str = ""

    @property
    def available_at(self) -> datetime:
        """A joined fact is usable only once every required source is available."""
        times = [timestamp(self.captured_at), timestamp(self.observed_at)]
        if self.data.get("_catalog_event_time"):
            times.append(timestamp(self.data["_catalog_event_time"]))
        return max(times)

    def eligible(self, cutoff: str) -> bool:
        return self.available_at <= timestamp(cutoff)


def serialize_steps(steps: list[dict]) -> list[dict]:
    def key(step):
        phase = step["phase"]
        return list(OPERATIONS).index(phase), OPERATIONS[phase].index(step["operation"]), step["system_id"], step["resource_id"]
    result = []
    seen = set()
    for step in sorted(steps, key=key):
        unique = (step["phase"], step["operation"], step["system_id"], step["resource_id"])
        if unique in seen:
            continue
        seen.add(unique)
        result.append({"step_no": len(result) + 1, **{name: step[name] for name in ("phase", "system_id", "resource_id", "operation", "state", "evidence_id")}})
    return result


def _steps_json(text: str) -> list:
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON object field")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("Nonstandard JSON numeric constant")

    if not isinstance(text, str):
        raise ValueError("steps_json must be a JSON-encoded string")
    steps = json.loads(text, object_pairs_hook=unique_keys, parse_constant=reject_constant)
    if not isinstance(steps, list):
        raise ValueError("steps_json must encode an array")
    return steps


def validate_output(rows: list[dict], requests: list[dict]) -> None:
    """Validate serialization and plan coverage, without asserting prediction accuracy."""
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"case_id", "deletion_status", "steps_json"}:
            raise ValueError("Output columns differ from the contract")
        if any(not isinstance(row[field], str) or not row[field].strip() for field in row):
            raise ValueError("Output values must be nonempty strings")
    if any(not isinstance(request.get("case_id"), str) or not request["case_id"].strip() for request in requests):
        raise ValueError("Requests must have nonempty string case IDs")
    expected = sorted(request["case_id"] for request in requests)
    if [row["case_id"] for row in rows] != expected or len(set(expected)) != len(expected):
        raise ValueError("Output must contain each requested case exactly once in sorted order")
    for row in rows:
        status = row["deletion_status"]
        if status not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}:
            raise ValueError("Unknown deletion status")
        steps = _steps_json(row["steps_json"])
        if status == "NOT_APPLICABLE" and steps:
            raise ValueError("Non-deletion requests require an empty array")
        if status != "NOT_APPLICABLE" and not steps:
            raise ValueError("Deletion decisions require a nonempty evidence-backed plan")
        for number, step in enumerate(steps, 1):
            if not isinstance(step, dict) or set(step) != STEP_FIELDS or type(step["step_no"]) is not int or step["step_no"] != number:
                raise ValueError("Invalid step fields or numbering")
            for field in STEP_FIELDS - {"step_no"}:
                value = step[field]
                if not isinstance(value, str) or value != value.strip() or (field != "evidence_id" and not value):
                    raise ValueError("Step fields must contain exact string values")
            if step["phase"] not in OPERATIONS or step["operation"] not in OPERATIONS[step["phase"]] or STATES[step["operation"]] != step["state"]:
                raise ValueError("Invalid phase, operation, or state")
            backed = step["phase"] == "FINDING" or status == "COMPLETE"
            if bool(step["evidence_id"]) != backed:
                raise ValueError("Invalid evidence citation for step")
            if status == "COMPLETE" and step["phase"] != "VERIFICATION":
                raise ValueError("Complete cases contain verification only")
        if steps != serialize_steps(steps):
            raise ValueError("Steps are not in canonical order")
        if status == "INCOMPLETE":
            by_phase = {phase: {} for phase in OPERATIONS}
            for step in steps:
                key = (step["system_id"], step["resource_id"])
                by_phase[step["phase"]].setdefault(key, set()).add(step["operation"])
            if not all(by_phase.values()):
                raise ValueError("Incomplete cases require findings, remediation, and verification")
            for key, findings in by_phase["FINDING"].items():
                remedies = by_phase["REMEDIATION"].get(key, set())
                if any(not FINDING_REMEDIATIONS[finding].intersection(remedies) for finding in findings):
                    raise ValueError("Every finding requires a matching remediation for the same resource")
            for key, remedies in by_phase["REMEDIATION"].items():
                findings = by_phase["FINDING"].get(key, set())
                allowed = set().union(*(FINDING_REMEDIATIONS[finding] for finding in findings))
                if not remedies <= allowed:
                    raise ValueError("Remediation requires a supporting finding for the same resource")
                required = {REMEDIATION_VERIFICATIONS[remedy] for remedy in remedies}
                if not required <= by_phase["VERIFICATION"].get(key, set()):
                    raise ValueError("Every remediation requires its matching verification")


def validate_citations(rows: list[dict], requests: list[dict], manifest, activities=(), history=(), observations=()) -> None:
    """Check visible citation IDs and time eligibility, never workflow-result claims.

    Matching observations, when supplied, additionally check observation timestamps.
    A missing observation match is permitted because complete snapshot scopes can
    prove absence without a record row. The reasoning layer must establish those
    scopes and all other semantic support; this check alone cannot prove a state.
    """
    validate_output(rows, requests)
    evidence = {}
    for records, id_field, time_field in ((manifest, "file_id", "captured_at"),
                                           (activities, "activity_id", "event_time"),
                                           (history, "audit_id", "event_time")):
        for record in records:
            identifier = record[id_field]
            if not isinstance(identifier, str) or not identifier or identifier in evidence:
                raise ValueError("Evidence IDs must be nonempty and unique")
            evidence[identifier] = timestamp(record[time_field])
    observation_index = {}
    for observation in observations:
        key = (observation.evidence_id, observation.system, observation.resource)
        observation_index.setdefault(key, []).append(observation)
    cutoffs = {request["case_id"]: request["audit_at"] for request in requests}
    for row in rows:
        cutoff = cutoffs[row["case_id"]]
        limit = timestamp(cutoff)
        for step in _steps_json(row["steps_json"]):
            identifier = step["evidence_id"]
            if not identifier:
                continue
            if identifier not in evidence:
                raise ValueError("Citation does not reference participant-visible evidence")
            if evidence[identifier] > limit:
                raise ValueError("Citation was captured or recorded after audit_at")
            matches = observation_index.get((identifier, step["system_id"], step["resource_id"]), [])
            if matches and not any(observation.eligible(cutoff) for observation in matches):
                raise ValueError("Cited resource was only observed after audit_at")


def write_output(path: Path, rows: list[dict], requests: list[dict]) -> None:
    rows = sorted(rows, key=lambda row: row["case_id"])
    validate_output(rows, requests)
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(rows)
