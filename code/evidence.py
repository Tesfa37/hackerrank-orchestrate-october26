"""Generic adapters for participant-visible business artifacts, with provenance."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from audit_core import Observation, norm, read_csv, timestamp

PREFIXES = {
    "data_flow_": ("integration_service", "DATA_FLOW"), "audit_record_": ("security_service", "SECURITY_AUDIT_LOG"),
    "legal_hold_": ("legal_service", "LEGAL_HOLD_RECORD"), "tombstone_": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "account_": ("account_service", "USER_PROFILE"), "search_": ("search_service", "SEARCH_INDEX_ENTRY"),
    "analytics_": ("analytics_platform", "ANALYTICS_PROFILE"), "backup_": ("backup_service", "BACKUP_ARCHIVE"),
    "export_": ("export_service", "USER_EXPORT"), "support_": ("support_platform", "SUPPORT_MESSAGE"),
    "cache_": ("cache_service", "CACHE_ENTRY"), "marketing_": ("marketing_platform", "MARKETING_PROFILE"),
    "email_delivery_": ("email_delivery_service", "EMAIL_DELIVERY_LOG"), "identifier_": ("identity_service", "SECONDARY_IDENTIFIER"),
}
ALIASES = {"profile_service": "account_service", "support_replica": "support_platform", "search_index_service": "search_service"}
IDENTIFIER_KEYS = {"email", "email_hash", "phone", "user_id", "customer_reference", "subject_reference", "subject_ref", "subject_key", "subject_selector", "lookup_key", "lookup_value", "match_key", "correlation_key", "matched_value", "query", "owner_email", "owner_phone", "customer_email", "requester_email", "requester_phone", "uploaded_by"}
DIRECT_KEYS = {"email", "email_hash", "phone", "name", "full_name", "display_name", "owner_email", "owner_phone", "customer_email", "requester_email", "requester_phone", "requester_name"}
RESULTS = {"NOT_FOUND": "ABSENT", "ABSENT": "ABSENT", "FOUND": "PRESENT", "PRESENT": "PRESENT", "IDENTIFIABLE": "PRESENT", "REDACTED": "REDACTED", "ANONYMIZED": "ANONYMIZED", "DISABLED": "DISABLED", "BLOCKED": "BLOCKED", "ENABLED": "ACTIVE", "ACTIVE": "ACTIVE", "RESTORABLE": "ACTIVE"}


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from strings(value)


def identifiers(obj) -> set[str]:
    found = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in IDENTIFIER_KEYS and isinstance(value, (str, int)) and str(value).lower() not in {"null", "none", "[redacted]", "redacted", ""}:
                found.add(norm(value))
            if isinstance(value, (dict, list)):
                found.update(identifiers(value))
    elif isinstance(obj, list):
        for value in obj:
            found.update(identifiers(value))
    for text in strings(obj):
        found.update(norm(x) for x in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text))
        found.update(re.findall(r"\buser_[A-Za-z0-9]+\b", text))
        found.update(re.findall(r"\b[a-f0-9]{64}\b", text))
    return found


def resource_kind(resource: str, collection: str = "", explicit: str = "") -> tuple[str, str]:
    system, category = next((value for prefix, value in PREFIXES.items() if resource.startswith(prefix)), ("", ""))
    context = collection.lower()
    if "attachment" in context:
        category = "SUPPORT_ATTACHMENT"
    elif "contact_query" in context or "legacy_contact_index" in context or "secondary_identifier" in context:
        category = "SECONDARY_IDENTIFIER"
    if explicit:
        category = explicit
    return system, category


def infer_state(data: dict, category: str) -> str:
    result = str(data.get("result", data.get("state", ""))).upper()
    if result in RESULTS:
        return RESULTS[result]
    if data.get("status_code", data.get("http_status")) in (404, "404"):
        return "ABSENT"
    if "rows" in data and str(data["rows"]) == "0":
        return "ABSENT"
    if "hits" in data:
        hits = data["hits"]
        total = hits.get("total", 0) if isinstance(hits, dict) else hits
        return "ABSENT" if total in (0, "0") else "PRESENT"
    if result in {"MISS", "EMPTY"} or str(data.get("total_hits", "")) == "0":
        return "ABSENT"
    if category == "DATA_FLOW":
        enabled = data.get("enabled", data.get("active"))
        if enabled is not None:
            return "ACTIVE" if str(enabled).lower() in {"true", "1", "enabled"} else "DISABLED"
    if category == "BACKUP_ARCHIVE":
        allowed = data.get("restore_allowed")
        if allowed is not None:
            return "ACTIVE" if str(allowed).lower() in {"true", "1", "allowed"} else "BLOCKED"
    if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
        return "PRESENT" if identifiers({k: v for k, v in data.items() if k not in {"lookup_key", "query", "correlation_key", "matched_value"}}) else "ANONYMIZED"
    if category in {"SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE", "EMAIL_DELIVERY_LOG"}:
        def exposed(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in DIRECT_KEYS and value and str(value).lower() not in {"null", "none", "[redacted]", "redacted"}:
                        return True
                    if isinstance(value, (dict, list)) and exposed(value):
                        return True
                    if key in {"message_text", "message_excerpt", "body", "text"} and isinstance(value, str) and re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", value):
                        return True
            elif isinstance(obj, list):
                return any(exposed(item) for item in obj)
            return False
        if data.get("pii_detected") in (True, "true") or data.get("matched_value"):
            return "PRESENT"
        return "PRESENT" if exposed(data) else "REDACTED"
    return "PRESENT"


def make_observation(record: dict, meta: dict, system="", collection="", observed="", scope="") -> Observation | None:
    resource = str(record.get("resource_id", ""))
    if not resource:
        return None
    inferred_system, category = resource_kind(resource, collection, record.get("record_type", record.get("category", "")))
    system = record.get("system", record.get("system_id", system)) or inferred_system
    system = ALIASES.get(system, system)
    if not category or not system:
        return None
    when = record.get("observed_at", record.get("recorded_at", observed or meta["captured_at"]))
    return Observation(system, resource, category, infer_state(record, category), meta["file_id"], meta["captured_at"], when, identifiers(record), record, scope)


def parse_json(obj: dict, meta: dict):
    observations, scopes = [], []

    def walk(value, system="", collection="", observed="", parent_key=""):
        if isinstance(value, dict):
            system = value.get("data_store", value.get("system", system))
            collection = value.get("collection", collection)
            observed = value.get("captured_at", value.get("observed_at", value.get("recorded_at", observed)))
            if "resource_id" in value:
                observation = make_observation(value, meta, system, collection, observed)
                if observation:
                    observations.append(observation)
                return
            records = value.get("records")
            if isinstance(records, list) and collection and system:
                resources = {str(row["resource_id"]) for row in records if "resource_id" in row}
                _, category = resource_kind(next(iter(resources), ""), collection)
                category = category or category_for_table(collection)
                if category:
                    scopes.append({"system": system, "category": category, "scope": collection, "resources": resources, "evidence_id": meta["file_id"], "captured_at": meta["captured_at"], "observed_at": observed or meta["captured_at"]})
            for key, child in value.items():
                if key == "service_exports" and isinstance(child, dict):
                    for service, export in child.items():
                        walk(export, service, "", observed)
                elif isinstance(child, (dict, list)):
                    walk(child, system, collection or (key if key != "records" else ""), observed, key)
        elif isinstance(value, list):
            for child in value:
                walk(child, system, collection, observed, parent_key)
    walk(obj)
    return observations, scopes


def category_for_table(name: str) -> str:
    name = name.lower()
    for token, category in [("tombstone", "ACCOUNT_TOMBSTONE"), ("deleted_customer", "ACCOUNT_TOMBSTONE"), ("audit", "SECURITY_AUDIT_LOG"), ("retained_order", "LEGAL_HOLD_RECORD"), ("legal", "LEGAL_HOLD_RECORD"), ("connector", "DATA_FLOW"), ("backup", "BACKUP_ARCHIVE"), ("restore", "BACKUP_ARCHIVE"), ("analytics", "ANALYTICS_PROFILE"), ("telemetry", "PRODUCT_TELEMETRY"), ("search", "SEARCH_INDEX_ENTRY"), ("attachment", "SUPPORT_ATTACHMENT"), ("support", "SUPPORT_MESSAGE"), ("export", "USER_EXPORT"), ("marketing", "MARKETING_PROFILE"), ("profile", "USER_PROFILE")]:
        if token in name:
            return category
    return ""


def parse_sql(text: str, meta: dict):
    observations, scopes = [], []
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    denied = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    db.set_authorizer(lambda action, arg1, arg2, database, source: sqlite3.SQLITE_DENY if action in denied or (action == sqlite3.SQLITE_FUNCTION and str(arg2).lower() == "load_extension") else sqlite3.SQLITE_OK)
    try:
        db.executescript(text)
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            if table == "snapshot_scope":
                continue
            quoted = '"' + table.replace('"', '""') + '"'
            records = [dict(row) for row in db.execute("SELECT * FROM " + quoted)]
            category = category_for_table(table)
            table_system = {"USER_PROFILE": "account_service", "SEARCH_INDEX_ENTRY": "search_service", "ANALYTICS_PROFILE": "analytics_platform", "SUPPORT_MESSAGE": "support_platform", "USER_EXPORT": "export_service", "DATA_FLOW": "integration_service", "BACKUP_ARCHIVE": "backup_service", "SECURITY_AUDIT_LOG": "security_service"}.get(category, "")
            groups = defaultdict(set)
            for row in records:
                if "record_json" in row:
                    record = json.loads(row["record_json"])
                    collection = row.get("collection_name", table)
                    system = row.get("origin_system", "")
                else:
                    record, collection, system = row, table, table_system
                observation = make_observation(record, meta, system, collection, meta["captured_at"], table)
                if observation:
                    observations.append(observation)
                    groups[(observation.system, observation.category)].add(observation.resource)
            if category and table_system:
                groups.setdefault((table_system, category), set())
            for (system, group_category), resources in groups.items():
                scopes.append({"system": system, "category": group_category, "scope": table, "resources": resources, "evidence_id": meta["file_id"], "captured_at": meta["captured_at"], "observed_at": meta["captured_at"]})
    finally:
        db.close()
    return observations, scopes


def parse_log(text: str, meta: dict):
    observations, traces = [], {}
    pair_pattern = re.compile(r'(\w+)=("(?:\\.|[^"\\])*"|\S+)')
    for line_number, line in enumerate(text.splitlines(), 1):
        time_match = re.match(r"(\d{4}-\d\d-\d\dT[\d:.]+Z)", line)
        if not time_match:
            continue
        observed = time_match[1]
        rest = line[len(observed):].strip()
        data = {}
        if rest.startswith("{"):
            try:
                data = json.loads(rest)
            except json.JSONDecodeError:
                continue
        else:
            for key, value in pair_pattern.findall(rest):
                if value.startswith('"'):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = value.strip('"')
                data[key] = value
            if "message" in data:
                for key, value in pair_pattern.findall(str(data["message"])):
                    data[key] = value.strip('"')
            bracket = re.match(r"\[\w+\]\s+\[([^]]+)\]\s+\[([^]]+)\]\s+(\w+):", rest)
            syslog = re.match(r"<\d+>\d+\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-", rest)
            if bracket:
                data.update(service=bracket[1], trace_id=bracket[2], event=bracket[3])
            elif syslog:
                data.setdefault("service", syslog[1]); data.setdefault("trace_id", syslog[2])
        trace_id = data.get("trace_id", data.get("requestId", ""))
        if trace_id:
            previous = traces.setdefault(trace_id, {})
            previous.update(data)
            data = dict(previous)
        resource = data.get("resource_id", "")
        event = str(data.get("event", ""))
        if not resource or event.endswith("_started") or event in {"cache_lookup", "connection_acquired", "consumer_lag", "thumbnail_failed", "deletion_marker_check"}:
            continue
        if not any(key in data for key in ("rows", "result", "enabled", "restore_allowed", "matched_value", "pii_detected", "email", "requester_email", "record_type", "integrity_check")):
            continue
        system = data.get("system", data.get("service", data.get("function", "")))
        data["observed_at"] = observed
        data["line_number"] = line_number
        observation = make_observation(data, meta, system, event + " " + str(data.get("source", "")), observed)
        if observation:
            observations.append(observation)
    return observations, []


class EvidenceStore:
    def __init__(self, observations=None, scopes=None, activities=None):
        self.observations = observations or []
        self.scopes = scopes or []
        self.activities = activities or []
        self.media = []
        self.by_resource = defaultdict(list)
        self.refresh()

    def refresh(self):
        self.by_resource.clear()
        for observation in self.observations:
            self.by_resource[observation.resource].append(observation)


def load_evidence(dataset: Path, model_client=None) -> EvidenceStore:
    store = EvidenceStore(activities=read_csv(dataset / "system_activity.csv"))
    for meta in read_csv(dataset / "evidence_files.csv"):
        path = (dataset / meta["file_path"]).resolve()
        if not path.is_relative_to(dataset.resolve()):
            raise ValueError("Evidence path escapes dataset")
        if path.suffix == ".json":
            observations, scopes = parse_json(json.loads(path.read_text(encoding="utf-8")), meta)
        elif path.suffix == ".sql":
            observations, scopes = parse_sql(path.read_text(encoding="utf-8"), meta)
        elif path.suffix == ".log":
            observations, scopes = parse_log(path.read_text(encoding="utf-8"), meta)
        elif path.suffix == ".txt":
            observations, scopes = [], []
            for line in path.read_text(encoding="utf-8").splitlines():
                fields = [x.strip() for x in line.removeprefix("- ").split("|")]
                if len(fields) == 6 and re.match(r"\d{4}-", fields[0]):
                    record = dict(zip(["observed_at", "system", "resource_id", "record_type", "result", "subject_reference"], fields))
                    observation = make_observation(record, meta)
                    if observation:
                        observations.append(observation)
        elif path.suffix in {".png", ".pdf"}:
            store.media.append((path, meta))
            observations, scopes = [], []
        else:
            raise ValueError(f"Unsupported evidence format: {path.suffix}")
        store.observations.extend(observations)
        store.scopes.extend(scopes)
    store.refresh()
    return store
