"""Shared input, identity, observation, and exact-output contract primitives."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
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


def read_csv(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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
        for row in self.snapshots:
            history = self.history.get(row["user_id"], [])
            current = dict(row)
            for change in sorted(history, key=lambda item: item["event_time"], reverse=True):
                if timestamp(change["event_time"]) > timestamp(cutoff):
                    current[change["field_name"]] = change["old_value"]
            values = {norm(current.get(key)) for key in ("user_id", "email", "phone", "email_hash")}
            names = {current.get("name", "")}
            for change in history:
                if timestamp(change["event_time"]) <= timestamp(cutoff):
                    if change["field_name"] == "name":
                        names.update([change["old_value"], change["new_value"]])
                    else:
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

    def eligible(self, cutoff: str) -> bool:
        limit = timestamp(cutoff)
        return timestamp(self.captured_at) <= limit and timestamp(self.observed_at) <= limit


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


def validate_output(rows: list[dict], requests: list[dict]) -> None:
    expected = sorted(row["case_id"] for row in requests)
    if [row["case_id"] for row in rows] != expected or len(set(expected)) != len(expected):
        raise ValueError("Output must contain each requested case exactly once in sorted order")
    for row in rows:
        if set(row) != {"case_id", "deletion_status", "steps_json"}:
            raise ValueError("Output columns differ from the contract")
        status = row["deletion_status"]
        if status not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}:
            raise ValueError("Unknown deletion status")
        steps = json.loads(row["steps_json"])
        if not isinstance(steps, list) or (status == "NOT_APPLICABLE" and steps):
            raise ValueError("Non-deletion requests require an empty array")
        for number, step in enumerate(steps, 1):
            if set(step) != STEP_FIELDS or step["step_no"] != number:
                raise ValueError("Invalid step fields or numbering")
            if step["phase"] not in OPERATIONS or step["operation"] not in OPERATIONS[step["phase"]] or STATES[step["operation"]] != step["state"]:
                raise ValueError("Invalid phase, operation, or state")
            backed = step["phase"] == "FINDING" or status == "COMPLETE"
            if bool(step["evidence_id"]) != backed:
                raise ValueError("Invalid evidence citation for step")
            if status == "COMPLETE" and step["phase"] != "VERIFICATION":
                raise ValueError("Complete cases contain verification only")
        if steps != serialize_steps(steps):
            raise ValueError("Steps are not in canonical order")


def write_output(path: Path, rows: list[dict], requests: list[dict]) -> None:
    rows = sorted(rows, key=lambda row: row["case_id"])
    validate_output(rows, requests)
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(rows)
